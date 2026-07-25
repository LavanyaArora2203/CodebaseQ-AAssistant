from pathlib import Path

from repo_cloning import RepoCloner
from file_filtering import FileFilter
from language_detection import LanguageDetector


def main():

    # Replace with any public GitHub repository
    repo_url = "https://github.com/LavanyaArora2203/InboxAgent.git"

    cloner = RepoCloner()

    try:
        print("=" * 80)
        print("STEP 1 : CLONING REPOSITORY")
        print("=" * 80)

        repo_path = cloner.clone(repo_url)

        print(f"\nRepository cloned to:\n{repo_path}")

        print("\n")

        print("=" * 80)
        print("STEP 2 : FILTERING FILES")
        print("=" * 80)

        file_filter = FileFilter(repo_path)

        files = list(file_filter.get_indexable_files())

        print(f"\nIndexable files found: {len(files)}")

        print("\nFirst 20 files:\n")

        for file in files[:20]:
            print(file.relative_to(repo_path))

        print("\n")

        print("=" * 80)
        print("STEP 3 : LANGUAGE DETECTION")
        print("=" * 80)

        detector = LanguageDetector()

        for file in files[:20]:

            info = detector.detect(file)

            print("-" * 60)

            print(f"File : {file.relative_to(repo_path)}")

            if info:

                print(f"Language           : {info.language}")
                print(f"Extension          : {info.extension}")
                print(f"Tree-sitter Parser : {info.tree_sitter_supported}")

            else:

                print("Language : Unknown")

        print("\n")

        print("=" * 80)
        print("INGESTION COMPLETED SUCCESSFULLY")
        print("=" * 80)

    finally:
        cloner.cleanup()


if __name__ == "__main__":
    main()

##RUNNING##