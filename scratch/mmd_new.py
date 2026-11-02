def mmd_from_gram(K: np.ndarray, in_a: np.ndarray, same_prompt: np.ndarray) -> float:
    """MMD estimate for sample A = rows with in_a True, B = the rest.

    Each of the three terms is the mean kernel value over pairs that share a
    prompt (pairs with different prompts have kernel 0 and are not counted),
    and within-sample terms skip a sample paired with itself. This follows the
    authors' package (model_equality_testing.tests._mmd), which produced their
    reported results. The paper's eq. 4 instead divides by all pairs, N(N-1) and
    N^2; with several prompts the two are not proportional, so p-values can
    differ slightly. Either way the permutation test is valid; we match the
    package so results are comparable with theirs."""
    a, b = np.flatnonzero(in_a), np.flatnonzero(~in_a)

    def mean_same(rows, cols, within):
        k, s = K[np.ix_(rows, cols)], same_prompt[np.ix_(rows, cols)]
        total, count = k.sum(), s.sum()
        if within:
            total, count = total - np.trace(k), count - len(rows)
        return total / count if count > 0 else 0.0

    return float(mean_same(a, a, True) + mean_same(b, b, True) - 2.0 * mean_same(a, b, False))


