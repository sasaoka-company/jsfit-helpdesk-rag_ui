# app_ui.py
import streamlit as st
import requests
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from config import API_BASE_URL
from logger import get_logger

# ロガー設定
logger = get_logger(__name__)


def show_message(message: BaseMessage) -> None:
    """
    画面に会話履歴を表示
    """
    if isinstance(message, HumanMessage):
        st.chat_message("human").write(message.content)
    elif isinstance(message, AIMessage):
        # HTTP API経由の場合、tool_callsの詳細は見えないため、コンテンツのみ表示
        st.chat_message("ai").write(message.content)


def query_api(query: str) -> str:
    """
    FastAPIエンドポイントにHTTPリクエストを送信して回答を取得
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/query", json={"query": query}, timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result["answer"]
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return f"エラーが発生しました: {str(e)}"


def app():
    # 1. タイトルとAPI接続状況を表示
    st.title("業務上の質問に回答します！")

    # API接続確認
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            st.sidebar.success("✅ AIエージェントサーバーに接続されています")
        else:
            st.sidebar.warning("⚠️ AIエージェントサーバーとの接続に問題があります")
            logger.info(
                f"AIエージェントサーバーとの接続に問題があります。status_code: {response.status_code}"
            )
    except Exception as e:
        st.sidebar.error("❌ AIエージェントサーバーに接続できません")
        st.sidebar.info(
            "AIエージェントサーバーを起動してください:\n```\nuvicorn rag_api:app --reload\n```"
        )
        logger.error(f"エラーが発生しました: {e}")

    # 2. ここまでの会話履歴を表示
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        show_message(message)

    # 3. ユーザーの入力を受け付け
    if user_input := st.chat_input():
        # ユーザーメッセージを表示・保存
        st.chat_message("human").write(user_input)
        st.session_state.messages.append(HumanMessage(content=user_input))

        # 4. APIエンドポイントに質問を送信して回答を取得
        with st.chat_message("ai"):
            with st.spinner("回答を生成中..."):
                answer = query_api(user_input)
            st.write(answer)

        # AIの回答を保存
        st.session_state.messages.append(AIMessage(content=answer))


if __name__ == "__main__":
    app()
