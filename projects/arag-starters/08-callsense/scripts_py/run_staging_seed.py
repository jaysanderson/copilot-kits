import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import seed_staging as s  # noqa: E402


def main():
    print("=== 1/6 Labelsets ===")
    s.create_labelsets()

    print("\n=== 2/6 Ingest 24 resources ===")
    rid_by_slug = s.ingest_all()
    (Path(__file__).parent / "rid_map.json").write_text(__import__("json").dumps(rid_by_slug, indent=2))

    print("\n=== 3/6 Wait for PROCESSED ===")
    pending = s.wait_for_processed(rid_by_slug)
    if pending:
        print(f"WARNING: {len(pending)} resources never reached PROCESSED: {list(pending.keys())}")

    print("\n=== 4/6 Verify TRANSCRIPT paragraph coverage (count, never infer from PROCESSED) ===")
    counts, failures = s.verify_transcript_paragraphs(rid_by_slug)
    if failures:
        print(f"\n{len(failures)} media resource(s) missing TRANSCRIPT paragraphs on first pass: {failures}")
        print("Reprocessing and re-checking once...")
        for slug in failures:
            rid = rid_by_slug[slug]
            code = s.reprocess(rid)
            print(f"  reprocess {slug} -> HTTP {code}")
        import time
        time.sleep(20)
        counts2, failures2 = s.verify_transcript_paragraphs({k: rid_by_slug[k] for k in failures})
        still_failing = failures2
        if still_failing:
            print(f"\nSTILL FAILING after reprocess: {still_failing} - these need a fresh re-render + re-ingest.")
    else:
        print("\nAll media resources carry TRANSCRIPT paragraphs on first pass.")

    print("\n=== 5/6 Register + run DA tasks (chatgpt-azure-4o-mini, sequential) ===")
    task_ids = s.run_agents_sequentially()
    print("Task ids:", task_ids)

    print("\n=== Verify label coverage by direct resource read (facet aggregation banned) ===")
    s.verify_label_coverage(rid_by_slug)

    print("\n=== 6/6 Register search configurations ===")
    s.create_search_configs()

    print("\n=== DONE ===")
    print(f"Staging KB: {s.KB_ID}")


if __name__ == "__main__":
    main()
