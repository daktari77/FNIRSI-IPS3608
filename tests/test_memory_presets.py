import json
import tempfile
import unittest
from pathlib import Path

from ips3608_app.memory_presets import MemoryRepository


class MemoryPresetTests(unittest.TestCase):
    def test_memory_repository_loads_versioned_presets(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory_presets.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "presets": [
                            {
                                "slot_id": "M2",
                                "label": "Bench",
                                "voltage_v": 12.0,
                                "current_a": 1.5,
                                "enabled": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            presets = MemoryRepository(path).load_all()

        self.assertEqual(len(presets), 6)
        self.assertEqual(presets[1].slot_id, "M2")
        self.assertEqual(presets[1].display_name, "M2 - Bench")
        self.assertEqual(presets[1].voltage_v, 12.0)


if __name__ == "__main__":
    unittest.main()
