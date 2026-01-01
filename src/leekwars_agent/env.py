"""Gymnasium environment for LeekWars fights.

NOTE: Current implementation runs full fights (episodic).
For step-by-step RL training, we need Py4J integration.
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from pathlib import Path
from typing import Any

from .simulator import Simulator, EntityConfig, ScenarioConfig, FightOutcome


class LeekWarsEnv(gym.Env):
    """
    LeekWars fight environment.

    Current limitation: Runs full fights, not step-by-step.
    Use for policy evaluation, not training.

    Observation: Entity stats (HP%, MP, TP, position)
    Action: Not used in episodic mode (AI file determines behavior)
    Reward: +1 win, -1 loss, 0 draw
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        ai_path: str = "fighter_v1.leek",
        opponent_ai: str = "fighter_v1.leek",
        level: int = 1,
        render_mode: str | None = None,
    ):
        super().__init__()

        self.ai_path = ai_path
        self.opponent_ai = opponent_ai
        self.level = level
        self.render_mode = render_mode

        self.simulator = Simulator()
        self.last_outcome: FightOutcome | None = None
        self.episode_count = 0

        # Simplified observation: [my_hp%, enemy_hp%, my_mp, my_tp, distance]
        # In full episodic mode, observation is just initial state
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(5,), dtype=np.float32
        )

        # Action space placeholder - not used in episodic mode
        # In step-by-step mode, actions would be:
        # 0-7: move directions, 8: use weapon, 9: end turn
        self.action_space = spaces.Discrete(10)

    def _get_obs(self) -> np.ndarray:
        """Get observation from current state."""
        # In episodic mode, just return placeholder
        return np.array([1.0, 1.0, 0.3, 1.0, 0.5], dtype=np.float32)

    def _get_info(self) -> dict[str, Any]:
        """Get info dict."""
        info = {"episode": self.episode_count}
        if self.last_outcome:
            info.update({
                "winner": self.last_outcome.winner,
                "turns": self.last_outcome.turns,
                "duration_ms": self.last_outcome.duration_ms,
            })
        return info

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset environment for new episode."""
        super().reset(seed=seed)

        self.episode_count += 1
        self.last_outcome = None

        return self._get_obs(), self._get_info()

    def step(
        self, action: int
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """
        Run a full fight (episodic mode).

        In step-by-step mode (future), this would execute one action.
        """
        # Run full fight
        try:
            # Convert numpy int to Python int for JSON serialization
            seed = int(self.np_random.integers(0, 2**31)) if self.np_random else None
            self.last_outcome = self.simulator.run_1v1(
                self.ai_path,
                self.opponent_ai,
                level=self.level,
                seed=seed,
            )

            # Reward: +1 win, -1 loss, 0 draw
            if self.last_outcome.team1_won:
                reward = 1.0
            elif self.last_outcome.team2_won:
                reward = -1.0
            elif self.last_outcome.is_draw:
                reward = 0.0
            else:
                reward = 0.0

        except Exception as e:
            # Fight failed
            reward = -1.0
            self.last_outcome = None

        obs = self._get_obs()
        terminated = True  # Episode always ends after one fight
        truncated = False
        info = self._get_info()

        return obs, reward, terminated, truncated, info

    def render(self):
        """Render last fight outcome."""
        if self.render_mode == "human" and self.last_outcome:
            print(f"Fight #{self.episode_count}:")
            print(f"  Winner: Team {self.last_outcome.winner}")
            print(f"  Turns: {self.last_outcome.turns}")
            print(f"  Duration: {self.last_outcome.duration_ms:.0f}ms")


class LeekWarsEvalEnv(LeekWarsEnv):
    """
    Environment for evaluating policies.

    Runs N fights and tracks win rate.
    """

    def __init__(self, n_eval: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.n_eval = n_eval
        self.wins = 0
        self.losses = 0
        self.draws = 0

    def reset(self, **kwargs):
        self.wins = 0
        self.losses = 0
        self.draws = 0
        return super().reset(**kwargs)

    def evaluate(self) -> dict[str, float]:
        """Run N fights and return stats."""
        self.reset()

        for _ in range(self.n_eval):
            _, reward, _, _, _ = self.step(0)
            if reward > 0:
                self.wins += 1
            elif reward < 0:
                self.losses += 1
            else:
                self.draws += 1

        total = self.wins + self.losses + self.draws
        return {
            "win_rate": self.wins / total if total > 0 else 0,
            "loss_rate": self.losses / total if total > 0 else 0,
            "draw_rate": self.draws / total if total > 0 else 0,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
        }


def check_env():
    """Validate environment with SB3 checker."""
    from stable_baselines3.common.env_checker import check_env as sb3_check

    env = LeekWarsEnv()
    try:
        sb3_check(env)
        print("Environment check passed!")
        return True
    except Exception as e:
        print(f"Environment check failed: {e}")
        return False


if __name__ == "__main__":
    print("Checking environment...")
    check_env()

    print("\nRunning evaluation (5 fights)...")
    env = LeekWarsEvalEnv(n_eval=5)
    stats = env.evaluate()
    print(f"Results: {stats}")
