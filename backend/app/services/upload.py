MAGIC_BYTES = {
    "image/jpeg": b"\xff\xd8\xff",
    "image/png": b"\x89PNG",
    "image/gif": b"GIF8",
}


def validate_magic_bytes(content: bytes, content_type: str) -> None:
    expected = MAGIC_BYTES.get(content_type)
    if not expected:
        return

    if len(content) < len(expected) or content[: len(expected)] != expected:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件类型与扩展名不符",
        )
