#!/usr/bin/env python3
"""
HackerRank Orchestrate — Support Triage Agent
Entry point: reads support_tickets/support_tickets.csv, writes support_tickets/output.csv
Uses Groq (llama-3.3-70b-versatile) + local corpus retrieval (no pip installs needed)
"""

import os
import sys
import csv
import time
from pathlib import Path

from retriever import CorpusRetriever
from classifier import TriageAgent


def main():
    # Resolve paths relative to repo root (one level up from code/)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    input_path = repo_root / "support_tickets" / "support_tickets.csv"
    output_path = repo_root / "support_tickets" / "output.csv"
    data_path = repo_root / "data"

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)

    if not data_path.exists():
        print(f"[ERROR] Data directory not found: {data_path}")
        sys.exit(1)

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("[ERROR] GROQ_API_KEY environment variable not set.")
        print("  Get a free key at: https://console.groq.com/keys")
        sys.exit(1)

    print("[*] Loading corpus...")
    retriever = CorpusRetriever(data_path)
    print(f"    Loaded {retriever.doc_count()} document chunks from corpus.")

    agent = TriageAgent(api_key=api_key, retriever=retriever)

    output_columns = [
        "issue", "subject", "company",
        "response", "product_area", "status", "request_type", "justification"
    ]

    with open(input_path, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)

    print(f"[*] Processing {len(rows)} tickets...\n")

    results = []
    for i, row in enumerate(rows):
        issue = row.get("Issue", row.get("issue", "")).strip()
        subject = row.get("Subject", row.get("subject", "")).strip()
        company = row.get("Company", row.get("company", "None")).strip()

        label = subject[:60] if subject else issue[:60]
        print(f"  [{i+1}/{len(rows)}] {label}...")

        try:
            result = agent.triage(issue=issue, subject=subject, company=company)
        except Exception as e:
            print(f"    [WARN] Error on ticket {i+1}: {e}")
            result = {
                "response": "We were unable to process your request at this time. A support agent will follow up shortly.",
                "product_area": "General",
                "status": "escalated",
                "request_type": "product_issue",
                "justification": "Processing error — escalated for human review.",
            }

        results.append({
            "issue": issue,
            "subject": subject,
            "company": company,
            **result
        })

        # Small delay to stay comfortably within Groq free tier (30 req/min)
        if i < len(rows) - 1:
            time.sleep(2)

    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[✓] Done! Results written to: {output_path}")


if __name__ == "__main__":
    main()