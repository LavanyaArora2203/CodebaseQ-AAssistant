from chunking.metadata_extractor import MetadataExtractor
from chunking.ast_chunker import PythonTSChunker

filepath = "sample_repos\langchain\libs\langchain\scripts\check_imports.py"

# extractor = MetadataExtractor()

# source, tree, metadata = extractor.extract(filepath)

chunker = PythonTSChunker()

chunks = chunker.chunk_file(
    filepath,
    # tree,
    # metadata
)
from chunking.metadata_extractor import MetadataExtractor

extractor = MetadataExtractor()

for chunk in chunks:

    metadata = extractor.extract(

        file_path=chunk.file_path,

        chunk_type=chunk.chunk_type,

        start_line=chunk.start_line,

        end_line=chunk.end_line,

        function_name=chunk.name if chunk.chunk_type=="function" else None,

        class_name=chunk.name if chunk.chunk_type=="class" else None,

        parent_class=chunk.parent_class,

        language=chunk.language
    )

    print(metadata)

