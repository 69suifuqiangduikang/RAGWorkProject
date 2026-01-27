"""
RAG System Backend Module

支持多轮对话、灵活的检索控制和交互日志记录的RAG后端系统。
"""

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Callable
import yaml
import tempfile

# 动态添加 UltraRAG 到 Python 路径
_current_file = Path(__file__).resolve()
_ultrarag_src = _current_file.parent.parent / "UltraRAG" / "src"
if _ultrarag_src.exists() and str(_ultrarag_src) not in sys.path:
    sys.path.insert(0, str(_ultrarag_src))

try:
    from ultrarag.api import PipelineCall
except ImportError as e:
    print(f"错误: 无法导入 ultrarag 模块")
    print(f"请确保 UltraRAG 已正确安装，或者运行以下命令:")
    print(f"  cd /root/workspace/RAGWorkProject/UltraRAG && pip install -e .")
    raise


class RAGBackend:
    """RAG后端系统核心类"""
    
    def __init__(
        self,
        ultrarag_path: str,
        pipeline_file: str = "examples/bnu_visrag.yaml",
        parameter_file: str = "examples/parameter/bnu_visrag_parameter.yaml",
        log_dir: str = "config/logs",
        config_file: Optional[str] = None
    ):
        """
        初始化RAG后端
        
        Args:
            ultrarag_path: UltraRAG项目路径
            pipeline_file: Pipeline配置文件相对路径（注意：不要使用server/子目录中的文件）
            parameter_file: 参数配置文件相对路径
            log_dir: 日志保存目录
        """
        self.ultrarag_path = ultrarag_path
        self.pipeline_file = os.path.join(ultrarag_path, pipeline_file)
        self.parameter_file = os.path.join(ultrarag_path, parameter_file)
        self.log_dir = log_dir
        
        # 创建日志目录
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        # 当前会话信息
        self.session_id = str(uuid.uuid4())
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_start_time = datetime.now()

        # 配置文件路径与加载
        proj_root = Path(self.ultrarag_path).parent
        default_cfg = proj_root / "config" / "backend.yaml"
        self.config_path = Path(config_file) if config_file else default_cfg
        self.config: Dict[str, Any] = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"警告: 读取配置'{self.config_path}'失败: {e}")
        else:
            # 生成一个最小的占位配置，便于后续填写
            self.config = {
                "rag": {
                    "model": "",
                    "base_url": "",
                    "api_key": "ENV:OPENAI_API_KEY"
                },
                "no_retrieval": {
                    "model": "",
                    "base_url": "",
                    "api_key": "ENV:OPENAI_API_KEY"
                }
            }
        
    def query(
        self,
        query_text: str,
        use_retrieval: bool = True,
        top_k: int = 5,
        session_context: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        on_token: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        执行单轮RAG查询
        
        Args:
            query_text: 用户查询文本
            use_retrieval: 是否使用检索功能（True则使用RAG，False则仅使用LLM）
            top_k: 检索返回的文档数量
            session_context: 额外的会话上下文信息
            
        Returns:
            包含查询结果的字典，结构如下：
            {
                'query': str,  # 原始查询
                'answer': str,  # 生成的答案
                'retrieved_docs': List[Dict],  # 检索到的文档（如果use_retrieval=True）
                'use_retrieval': bool,  # 是否使用了检索
                'timestamp': str,  # 查询时间戳
                'turn_id': int  # 对话轮次ID
            }
        """
        turn_id = len(self.conversation_history)
        timestamp = datetime.now().isoformat()
        
        result = {
            'query': query_text,
            'use_retrieval': use_retrieval,
            'top_k': top_k,
            'timestamp': timestamp,
            'turn_id': turn_id,
            'session_context': session_context or {}
        }
        
        try:
            if use_retrieval:
                # 使用RAG进行检索和生成
                rag_result = self._run_rag_pipeline(query_text, top_k)
                answer = rag_result.get('answer', '')
                retrieved_docs = rag_result.get('retrieved_docs', [])
                
                result['answer'] = answer
                result['retrieved_docs'] = retrieved_docs
                result['full_rag_output'] = rag_result
                
                # 如果启用流式且Pipeline已有答案，则模拟流式输出（逐字符）
                if stream and answer:
                    for char in answer:
                        if on_token:
                            try:
                                on_token(char)
                            except Exception:
                                pass
            else:
                # 无检索生成：支持流式或非流式
                if stream:
                    final_text = []
                    for token in self.chat_no_retrieval_stream([{"role": "user", "content": query_text}]):
                        if on_token:
                            try:
                                on_token(token)
                            except Exception:
                                pass
                        final_text.append(token)
                    result['answer'] = ''.join(final_text)
                else:
                    result['answer'] = self.chat_no_retrieval([{"role": "user", "content": query_text}])
                result['retrieved_docs'] = []
            
            result['status'] = 'success'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['answer'] = None
            
        # 保存到对话历史
        self.conversation_history.append(result)
        
        return result
    
    def multi_turn_conversation(
        self,
        queries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        执行多轮对话
        
        Args:
            queries: 查询列表，每个查询是一个字典：
                {
                    'text': str,  # 查询文本
                    'use_retrieval': bool (可选，默认True),
                    'top_k': int (可选，默认5)
                }
                
        Returns:
            包含整个对话过程的结果
        """
        results = []
        
        for query_item in queries:
            query_text = query_item['text']
            use_retrieval = query_item.get('use_retrieval', True)
            top_k = query_item.get('top_k', 5)
            
            result = self.query(
                query_text=query_text,
                use_retrieval=use_retrieval,
                top_k=top_k,
                session_context={'total_turns': len(queries)}
            )
            results.append(result)
        
        return {
            'session_id': self.session_id,
            'total_turns': len(results),
            'results': results,
            'session_duration': (datetime.now() - self.session_start_time).total_seconds()
        }
    
    def _run_rag_pipeline(self, query_text: str, top_k: int = 5) -> Dict[str, Any]:
        """
        运行RAG Pipeline
        
        Args:
            query_text: 查询文本
            top_k: 检索返回的文档数量
            
        Returns:
            包含答案和检索文档的字典
        """
        # 创建临时查询文件
        temp_query_data = {
            "id": 0,
            "question": query_text,
            "golden_answers": [],
            "meta_data": {}
        }
        
        # 创建临时JSONL文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            json.dump(temp_query_data, f)
            temp_query_file = f.name
        
        try:
            # 动态修改参数文件以支持实时查询
            with open(self.parameter_file, 'r') as f:
                params = yaml.safe_load(f)
            
            # 更新基准参数
            if 'benchmark' in params:
                params['benchmark']['benchmark']['path'] = temp_query_file
            
            # 创建临时参数文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(params, f)
                temp_param_file = f.name
            
            try:
                # 保存当前工作目录
                original_cwd = os.getcwd()
                
                try:
                    # 切换到 UltraRAG 目录（PipelineCall 需要从此目录运行以找到 servers/）
                    os.chdir(self.ultrarag_path)
                    
                    # 运行Pipeline
                    result = PipelineCall(
                        pipeline_file=self.pipeline_file,
                        parameter_file=temp_param_file,
                        log_level="error"
                    )
                finally:
                    # 恢复原工作目录
                    os.chdir(original_cwd)
                
                # 解析结果
                answer = self._extract_answer(result)
                retrieved_docs = self._extract_retrieved_docs(result)
                
                return {
                    'answer': answer,
                    'retrieved_docs': retrieved_docs,
                    'raw_result': result
                }
            finally:
                # 清理临时参数文件
                if os.path.exists(temp_param_file):
                    os.remove(temp_param_file)
        finally:
            # 清理临时查询文件
            if os.path.exists(temp_query_file):
                os.remove(temp_query_file)
    
    def _run_llm_only(self, query_text: str) -> str:
        """
        仅使用LLM进行生成，不进行检索
        
        Args:
            query_text: 查询文本
            
        Returns:
            生成的答案
        """
        # 为兼容旧接口，转调无检索非流式接口
        return self.chat_no_retrieval([{"role": "user", "content": query_text}])

    def _get_api_key(self, key: Optional[str]) -> Optional[str]:
        """支持ENV:VAR格式从环境变量读取API Key"""
        if not key:
            return None
        if isinstance(key, str) and key.startswith("ENV:"):
            env_name = key.split(":", 1)[1]
            return os.environ.get(env_name)
        return key

    def _init_openai_client(self, mode: str = "no_retrieval"):
        """初始化OpenAI客户端，支持自定义base_url与api_key"""
        try:
            from openai import OpenAI
        except Exception as e:
            raise RuntimeError(f"缺少openai依赖，请先安装: pip install openai ({e})")

        cfg = self.config.get(mode, {})
        base_url = cfg.get("base_url") or None
        api_key = self._get_api_key(cfg.get("api_key"))
        # OpenAI新版SDK支持base_url, api_key传参
        client = OpenAI(base_url=base_url, api_key=api_key)
        return client, (cfg.get("model") or "")

    def chat_no_retrieval(self, messages: List[Dict[str, str]]) -> str:
        """
        无检索模式的多轮对话（非流式）
        messages: [{"role": "system"|"user"|"assistant", "content": str}, ...]
        """
        client, model = self._init_openai_client(mode="no_retrieval")
        if not model:
            raise RuntimeError("未配置no_retrieval.model，请在配置文件中设置")
        try:
            resp = client.chat.completions.create(model=model, messages=messages)
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"无检索对话失败: {e}")

    def chat_no_retrieval_stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """
        无检索模式的多轮对话（流式）
        以增量字符串迭代返回
        """
        client, model = self._init_openai_client(mode="no_retrieval")
        if not model:
            raise RuntimeError("未配置no_retrieval.model，请在配置文件中设置")
        try:
            stream = client.chat.completions.create(model=model, messages=messages, stream=True)
            for chunk in stream:
                delta = getattr(chunk.choices[0], "delta", None)
                if delta and getattr(delta, "content", None):
                    yield delta.content
        except Exception as e:
            raise RuntimeError(f"无检索流式对话失败: {e}")

    def generate_with_context(self, query_text: str, docs: List[Dict[str, Any]], mode: str = "rag") -> str:
        """基于检索文档进行非流式生成"""
        client, model = self._init_openai_client(mode=mode)
        if not model:
            raise RuntimeError("未配置rag.model，请在配置文件中设置")
        context_parts: List[str] = []
        for i, d in enumerate(docs[:10]):
            # 尽力提取文本字段
            txt = (
                d.get("text") or d.get("content") or d.get("passage") or d.get("chunk") or str(d)
            )
            context_parts.append(f"[Doc {i+1}]\n{txt}")
        context = "\n\n".join(context_parts) if context_parts else "(无检索上下文)"
        messages = [
            {"role": "system", "content": "你是一个严谨的助理，请结合提供的文档上下文回答问题，并在无法从上下文得到答案时明确说明。"},
            {"role": "user", "content": f"问题: {query_text}\n\n参考文档:\n{context}"}
        ]
        try:
            resp = client.chat.completions.create(model=model, messages=messages)
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"RAG生成失败: {e}")

    def generate_with_context_stream(self, query_text: str, docs: List[Dict[str, Any]], mode: str = "rag") -> Iterator[str]:
        """基于检索文档进行流式生成，返回token增量"""
        client, model = self._init_openai_client(mode=mode)
        if not model:
            raise RuntimeError("未配置rag.model，请在配置文件中设置")
        context_parts: List[str] = []
        for i, d in enumerate(docs[:10]):
            txt = (
                d.get("text") or d.get("content") or d.get("passage") or d.get("chunk") or str(d)
            )
            context_parts.append(f"[Doc {i+1}]\n{txt}")
        context = "\n\n".join(context_parts) if context_parts else "(无检索上下文)"
        messages = [
            {"role": "system", "content": "你是一个严谨的助理，请结合提供的文档上下文回答问题，并在无法从上下文得到答案时明确说明。"},
            {"role": "user", "content": f"问题: {query_text}\n\n参考文档:\n{context}"}
        ]
        try:
            stream = client.chat.completions.create(model=model, messages=messages, stream=True)
            for chunk in stream:
                delta = getattr(chunk.choices[0], "delta", None)
                if delta and getattr(delta, "content", None):
                    yield delta.content
        except Exception as e:
            raise RuntimeError(f"RAG流式生成失败: {e}")
    
    def _extract_answer(self, result: Dict[str, Any]) -> str:
        """从Pipeline结果中提取答案"""
        if isinstance(result, dict):
            # 尝试从不同的可能字段提取答案
            if 'final_result' in result:
                final = result['final_result']
                if isinstance(final, dict):
                    # 尝试从ans_ls中获取第一个答案（multimodal_generate输出格式）
                    if 'ans_ls' in final and isinstance(final['ans_ls'], list) and len(final['ans_ls']) > 0:
                        ans = final['ans_ls'][0]
                        if isinstance(ans, str):
                            return ans
                    # 尝试标准的answer字段
                    if 'answer' in final:
                        ans = final['answer']
                        if isinstance(ans, str):
                            return ans
                        # 如果answer是列表，取第一个
                        if isinstance(ans, list) and len(ans) > 0:
                            return str(ans[0])
                    if 'response' in final:
                        return str(final['response'])
                    # 尝试获取第一个非None值
                    for v in final.values():
                        if v and isinstance(v, str):
                            return v
            
            # 尝试直接访问答案字段
            if 'answer' in result:
                ans = result['answer']
                if isinstance(ans, str):
                    return ans
                if isinstance(ans, list) and len(ans) > 0:
                    return str(ans[0])
            if 'response' in result:
                return str(result['response'])
        
        return str(result)
    
    def _extract_retrieved_docs(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从Pipeline结果中提取检索到的文档"""
        retrieved_docs = []
        
        if isinstance(result, dict) and 'all_results' in result:
            all_results = result['all_results']
            if isinstance(all_results, list):
                for step_result in all_results:
                    if isinstance(step_result, dict):
                        if 'retrieved_docs' in step_result:
                            retrieved_docs = step_result['retrieved_docs']
                            break
                        if 'ret_psg' in step_result:
                            retrieved_docs = step_result['ret_psg']
                            break
        
        return retrieved_docs
    
    def save_session(self, custom_filename: Optional[str] = None) -> str:
        """
        保存当前会话的所有交互记录
        
        Args:
            custom_filename: 自定义文件名（不包含扩展名）
            
        Returns:
            保存的文件路径
        """
        if not custom_filename:
            custom_filename = f"session_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filepath = os.path.join(self.log_dir, f"{custom_filename}.json")
        
        session_data = {
            'session_id': self.session_id,
            'start_time': self.session_start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_turns': len(self.conversation_history),
            'conversation_history': self.conversation_history
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load_session(self, filepath: str) -> None:
        """
        加载之前保存的会话
        
        Args:
            filepath: 会话文件路径
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        self.session_id = session_data['session_id']
        self.conversation_history = session_data['conversation_history']
        # 不修改session_start_time，保持原始时间
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取当前对话的总结"""
        return {
            'session_id': self.session_id,
            'total_turns': len(self.conversation_history),
            'start_time': self.session_start_time.isoformat(),
            'current_time': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.session_start_time).total_seconds(),
            'turns': [
                {
                    'turn_id': turn['turn_id'],
                    'query': turn['query'],
                    'use_retrieval': turn['use_retrieval'],
                    'timestamp': turn['timestamp'],
                    'status': turn.get('status', 'unknown')
                }
                for turn in self.conversation_history
            ]
        }


if __name__ == "__main__":
    # 使用示例
    rag = RAGBackend(
        ultrarag_path="/root/workspace/RAGWorkProject/UltraRAG",
        log_dir="/root/workspace/RAGWorkProject/config/logs"
    )
    
    # 单轮查询示例
    result = rag.query(
        query_text="如何提交我写好的python训练程序？",
        use_retrieval=True,
        top_k=5
    )
    print("单轮查询结果:", result)
    
    # 多轮对话示例
    # multi_result = rag.multi_turn_conversation([
    #     {'text': '如何提交我写好的python训练程序？', 'use_retrieval': True},
    #     {'text': '有什么注意事项吗？', 'use_retrieval': False},
    #     {'text': '提交后多久会有反馈？', 'use_retrieval': True}
    # ])
    # print("多轮对话结果:", multi_result)
    
    # 保存会话
    saved_path = rag.save_session()
    print(f"会话已保存到: {saved_path}")
    
    # 获取对话总结
    summary = rag.get_conversation_summary()
    print("对话总结:", summary)
