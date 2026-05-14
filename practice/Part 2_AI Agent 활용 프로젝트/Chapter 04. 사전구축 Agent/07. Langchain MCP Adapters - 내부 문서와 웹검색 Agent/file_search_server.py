from mcp.server.fastmcp import FastMCP
import os
import stat
import time
from typing import List


mcp = FastMCP(
    "FileSearch",
    instructions="You are a local file searching assistant that can help with file searching tasks.",
    host="0.0.0.0",
    port=8000,
)


# 파일 목록 호출
@mcp.tool()
async def file_listup(directory: str) -> List[str]:
    """Returns a list of file names in the specified directory path."""
    try:
        return os.listdir(directory)
    except Exception as e:
        return [f"오류: {str(e)}"]


# 파일 검색 요약 및 정리 담당
@mcp.tool()
async def file_info(path: str) -> dict:
    """
    Returns detailed information about a file or directory at the given path.
    """
    if not os.path.exists(path):
        return {"error": f"경로 '{path}' 가 존재하지 않습니다."}

    try:
        stat_info = os.stat(path)

        file_type = "directory" if os.path.isdir(path) else "file"
        permissions = stat.filemode(stat_info.st_mode)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "path": os.path.abspath(path),
            "content": content,
            "type": file_type,
            "size": stat_info.st_size,  # bytes
            "created_time": time.ctime(stat_info.st_ctime),
            "modified_time": time.ctime(stat_info.st_mtime),
            "access_time": time.ctime(stat_info.st_atime),
            "permissions": permissions,
        }
    except Exception as e:
        return {"error": str(e)}


# 파일 쓰기 저장 담당
@mcp.tool()
async def save_file(content: str, output_path="file_info.md") -> str:
    """Writes the provided content to a text file at the specified output_path."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


if __name__ == "__main__":
    mcp.run(transport="sse")
