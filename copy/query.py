import openai
import feedparser
import requests
import os
from openai import OpenAI
from urllib.parse import quote


# ====== 配置 GPT 接口 ======

client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

# ====== 提取关键词 ======
def extract_keywords(user_input):
    system_prompt = (
        "你是一个科研助手，任务是从用户输入的一段话中提取3~5个用于arXiv搜索的英文关键词。"
        "输出格式为JSON数组，如：[\"keyword1\", \"keyword2\"]"
    )

    response = client.chat.completions.create(
        model="openai/chatgpt-4o-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        extra_headers={
            "HTTP-Referer": "https://your-site.com",  # 可选，用于 OpenRouter 统计
            "X-Title": "ArxivQueryTool"              # 可选，项目名称
        }
    )

    content = response.choices[0].message.content.strip()

    try:
        import json
        keywords = json.loads(content)
        return keywords
    except Exception as e:
        print(f"❌ 解析关键词失败，返回内容为：{content}")
        raise e


# ====== 搜索 arXiv 并下载 PDF ======
def search_arxiv_and_download(keywords, max_results=5, download_dir="arxiv_papers"):
    os.makedirs(download_dir, exist_ok=True)

    for keyword in keywords:
        print(f"\n🔍 Searching for: {keyword}")
        base_url = "http://export.arxiv.org/api/query?"
        encoded_keyword = quote(keyword)
        query_url = f"{base_url}search_query=all:{encoded_keyword}&start=0&max_results={max_results}"
        
        feed = feedparser.parse(query_url)
        if not feed.entries:
            print(f"❌ No results for: {keyword}")
            continue

        for i, entry in enumerate(feed.entries):
            title = entry.title
            authors = ', '.join(author.name for author in entry.authors)
            summary = entry.summary.strip().replace("\n", " ")
            published = entry.published
            pdf_url = next((l.href for l in entry.links if l.type == "application/pdf"), None)

            print(f"\n📄 Paper {i+1}")
            print(f"Title: {title}")
            print(f"Authors: {authors}")
            print(f"Published: {published}")
            print(f"PDF Link: {pdf_url}")

            # 下载 PDF
            if pdf_url:
                try:
                    pdf_response = requests.get(pdf_url)
                    safe_title = "".join(c for c in title if c.isalnum() or c in " _-").rstrip()
                    pdf_path = os.path.join(download_dir, f"{safe_title[:100]}.pdf")
                    with open(pdf_path, "wb") as f:
                        f.write(pdf_response.content)
                    print(f"📥 Saved to: {pdf_path}")
                except Exception as e:
                    print(f"⚠️ Error downloading PDF: {e}")


# ====== 主程序入口 ======
def main():
    print("🎯 欢迎使用 arXiv 智能搜索助手")
    user_sentence = input("请输入你想查询的一段话：\n> ")
    
    try:
        keywords = extract_keywords(user_sentence)
    except Exception as e:
        print(f"❌ 关键词提取失败：{e}")
        return

    print("\n🧠 GPT推荐的关键词如下：")
    for i, kw in enumerate(keywords):
        print(f"{i+1}. {kw}")

    selected = input("\n请输入你想使用的关键词编号（可多选，用逗号分隔，如1,3）：\n> ")
    try:
        chosen_keywords = [keywords[int(i.strip()) - 1] for i in selected.split(",")]
    except:
        print("❌ 输入格式有误，请输入有效编号。")
        return

    search_arxiv_and_download(chosen_keywords, max_results=5)


# ====== 启动 ======
if __name__ == "__main__":
    main()
