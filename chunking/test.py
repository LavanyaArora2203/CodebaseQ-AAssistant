from pathlib import Path

from models import ChunkMetadata, CodeChunk
from chunk_merger import ChunkMerger


def make_chunk(name, size):

    code = (
        f"def {name}():\n"
        + "    pass\n" * size
    )

    metadata = ChunkMetadata(
        file_path=Path("example.py"),
        language="python",

        symbol_name=name,
        symbol_type="function",

        parent_class=None,

        start_line=1,
        end_line=size,

        start_byte=0,
        end_byte=len(code),
    )

    return CodeChunk(
        source_code=code,
        metadata=metadata,
    )


chunks = [

    make_chunk("a", 3),
    make_chunk("b", 3),
    make_chunk("c", 3),
    make_chunk("large", 70),
    make_chunk("d", 5),
]

merger = ChunkMerger(
    max_tokens=120
)

merged = merger.merge(chunks)

print("=" * 70)

print("Original :", len(chunks))

print("Merged   :", len(merged))

print("=" * 70)

for i, chunk in enumerate(merged, 1):

    print()

    print(f"Chunk {i}")

    print("-" * 40)

    print("Tokens :", chunk.metadata.token_count)

    print("Lines  :", chunk.metadata.start_line,
          "-", chunk.metadata.end_line)

    print(chunk.source_code[:150], "...")