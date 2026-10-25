def think_time(cfg, remaining_ms, increment_ms=0):
    available = max(1, remaining_ms - cfg.move_overhead_ms)
    budget = available / cfg.moves_to_go + increment_ms * cfg.increment_fraction
    return max(1, int(min(budget, available / 3)))
