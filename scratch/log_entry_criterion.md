## 2026-11-02 (09:10): how Youssef et al. score reversal (settled), and our dev result reproduces theirs

From the paper (arXiv:2505.20819v2, Sec. 5.3): reversal and editing accuracy are agreement between the model's output after the intervention and the original (or edited) output, and "for reversal accuracy, we approximate the model's outputs using the next token prediction". So **their reversal accuracy is first-token**. Their headline Qwen2.5-7B ROME number, 62.90% at k=10 (Table 2, 310 successful edits, 31 relations), is first-token, with editing accuracy still 27.42% at that k. They generate 5 greedy tokens only for the qualitative examples (Table 4), which they describe as "semantically similar", not identical, to the originals.

**Our dev sweep on Qwen2.5-1.5B, same criterion:** first-token reversal 0.68 at q = 7-10 with the edit still present in 26%. That matches their 7B numbers closely, so the setup reproduces their method faithfully. On our stricter criterion (all 5 tokens equal to base) the best is 0.32 at q = 3.

Their own Table 3 also shows Qwen2.5-7B's output distribution is not recovered: mean KL to the original model on the edited prompt drops from 8.99 to 1.53 at best, not to ~0. That is consistent with the return-to-fact vs return-to-model point, from their own numbers.

**Correction to this morning's triage of the Gemini notes:** "paper scores first token only" was filed as wrong. The paper says it does score the first token. The other items in that list are unaffected.

**For the write-up:** compare like with like. Report our first-token number next to theirs (reproduction), then the 5-token and all-probes numbers as the stricter return-to-model view.

