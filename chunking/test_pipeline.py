from pathlib import Path

from ingestion.repo_cloning import RepoCloner

from pipeline import ChunkingPipeline


def main():

    repo_url = "https://github.com/LavanyaArora2203/InboxAgent.git"

    cloner = RepoCloner()

    try:

        print("=" * 80)
        print("CLONING REPOSITORY")
        print("=" * 80)

        repo_path = cloner.clone(repo_url)

        print(repo_path)

        print()

        pipeline = ChunkingPipeline(
            repository_root=repo_path,
            repository_name="flask",
            max_tokens=300,
        )

        chunks = pipeline.run()

        print()

        print("=" * 80)
        print("RESULTS")
        print("=" * 80)

        print(f"Total Chunks : {len(chunks)}")

        print()

        for item in chunks[:10]:

            chunk = item["chunk"]
            metadata = item["metadata"]

            print("-" * 80)

            print(
                f"{metadata['symbol_type']} : "
                f"{metadata['symbol_name']}"
            )

            print(
                f"{metadata['file_path']}"
            )

            print(
                f"Lines : "
                f"{metadata['start_line']}"
                f"-"
                f"{metadata['end_line']}"
            )

            print(
                f"Tokens : "
                f"{metadata['token_count']}"
            )

            print()

            print(chunk.source_code[:300])

            print()

    finally:

        cloner.cleanup()


if __name__ == "__main__":
    main()