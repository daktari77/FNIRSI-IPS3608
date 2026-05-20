import json
import tempfile
import unittest
from pathlib import Path

from ips3608_app.models import RoutineDefinition, RoutineState, RoutineStep
from ips3608_app.routines import ActiveRoutineRunner, RoutineRepository


class RoutineTests(unittest.TestCase):
    def test_routine_repository_loads_versioned_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ips3608_routines.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "routines": [
                            {
                                "name": "Ramp",
                                "steps": [
                                    {
                                        "voltage_start_v": 1.0,
                                        "voltage_end_v": 2.0,
                                        "current_start_a": 0.1,
                                        "current_end_a": 0.2,
                                        "duration_s": 5.0,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            routines = RoutineRepository(path).load_all()

        self.assertEqual(len(routines), 1)
        self.assertEqual(routines[0].name, "Ramp")
        self.assertEqual(routines[0].steps[0].voltage_v, 2.0)
        self.assertEqual(routines[0].steps[0].current_a, 0.2)

    def test_active_routine_completes_after_duration(self):
        routine = RoutineDefinition(
            name="Short",
            steps=[RoutineStep(voltage_v=2.0, current_a=0.2, duration_s=1.0)],
        )
        runner = ActiveRoutineRunner(routine)
        runner.start()
        runner._start_mono -= 2.0

        self.assertIsNone(runner.tick())
        self.assertEqual(runner.state, RoutineState.COMPLETED)


if __name__ == "__main__":
    unittest.main()
