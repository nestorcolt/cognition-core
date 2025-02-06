from crewai.memory.long_term.long_term_memory import LongTermMemory
from crewai.memory.long_term.long_term_memory_item import LongTermMemoryItem
from psycopg2.extras import DictCursor
from crewai.utilities import Printer
from datetime import datetime as dt
from typing import Dict, List, Any
import psycopg2
import json


class LTMPostgresStorage:
    """PostgreSQL storage class for LTM data storage."""

    def __init__(
        self,
        connection_string: str,
    ) -> None:
        self.connection_string = connection_string
        self._printer = Printer()
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the PostgreSQL database and create LTM table."""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS long_term_memories (
                            id SERIAL PRIMARY KEY,
                            task_description TEXT,
                            metadata JSONB,
                            datetime TEXT,
                            score FLOAT
                        )
                        """
                    )
                conn.commit()
        except Exception as e:
            self._printer.print(
                content=f"MEMORY ERROR: Database initialization failed: {e}",
                color="red",
            )

    def save(
        self,
        task_description: str,
        metadata: Dict[str, Any],
        datetime: str,
        score: float,
    ) -> None:
        try:
            # Convert Unix timestamp to ISO format
            formatted_datetime = dt.fromtimestamp(float(datetime)).isoformat()

            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO long_term_memories 
                        (task_description, metadata, datetime, score)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            task_description,
                            json.dumps(metadata),
                            formatted_datetime,
                            score,
                        ),
                    )
                conn.commit()
        except Exception as e:
            self._printer.print(
                content=f"MEMORY ERROR: Save operation failed: {e}",
                color="red",
            )

    def load(self, task_description: str, latest_n: int) -> List[Dict[str, Any]]:
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=DictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT task_description, metadata, datetime, score
                        FROM long_term_memories
                        WHERE task_description LIKE %s
                        ORDER BY datetime DESC
                        LIMIT %s
                        """,
                        (f"%{task_description}%", latest_n),
                    )
                    rows = cursor.fetchall()
                    return [
                        {
                            "task": row["task_description"],
                            "metadata": row["metadata"],
                            "datetime": row["datetime"],
                            "score": row["score"],
                        }
                        for row in rows
                    ]
        except Exception as e:
            self._printer.print(
                content=f"MEMORY ERROR: Load operation failed: {e}",
                color="red",
            )
            return []

    def reset(self) -> None:
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM long_term_memories")
                conn.commit()
        except Exception as e:
            self._printer.print(
                content=f"MEMORY ERROR: Reset operation failed: {e}",
                color="red",
            )


# Remove BaseStorageHandler and ExternalSQLHandler classes
# Keep CustomLongTermMemory but simplify it
class CustomLongTermMemory(LongTermMemory):
    def __init__(self, connection_string: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = LTMPostgresStorage(connection_string)

    def save(self, item: LongTermMemoryItem):
        metadata = item.metadata.copy()
        metadata.update({"agent": item.agent, "expected_output": item.expected_output})

        self.storage.save(
            task_description=item.task,
            metadata=metadata,
            datetime=item.datetime,
            score=metadata.get("quality", 0.0),
        )

    def search(self, task: str, latest_n: int = 3) -> List[Dict]:
        return self.storage.load(task, latest_n)
