from pathlib import Path
import aiosqlite


class Database:
    """Toutes les préférences sont isolées par guild_id."""

    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def initialize(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        await self.conn.execute("PRAGMA journal_mode=WAL")

        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS personal_voices (
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                voice_id TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            )
        """)

        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id TEXT PRIMARY KEY,
                timeout_minutes INTEGER NOT NULL DEFAULT 30,
                confirmation_messages_enabled INTEGER NOT NULL DEFAULT 1
            )
        """)

        # Migration des bases existantes : ajoute la colonne sans toucher
        # aux voix personnelles ni aux délais déjà enregistrés.
        async with self.conn.execute("PRAGMA table_info(guild_settings)") as cur:
            columns = await cur.fetchall()

        column_names = {row[1] for row in columns}
        if "confirmation_messages_enabled" not in column_names:
            await self.conn.execute("""
                ALTER TABLE guild_settings
                ADD COLUMN confirmation_messages_enabled INTEGER NOT NULL DEFAULT 1
            """)

        await self.conn.commit()

    async def get_voice(self, guild_id: int, user_id: int) -> str | None:
        async with self.conn.execute(
            "SELECT voice_id FROM personal_voices WHERE guild_id=? AND user_id=?",
            (str(guild_id), str(user_id)),
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else None

    async def set_voice(self, guild_id: int, user_id: int, voice_id: str):
        await self.conn.execute("""
            INSERT INTO personal_voices(guild_id, user_id, voice_id)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                voice_id=excluded.voice_id, updated_at=CURRENT_TIMESTAMP
        """, (str(guild_id), str(user_id), voice_id))
        await self.conn.commit()

    async def get_timeout(self, guild_id: int, default: int = 30) -> int:
        async with self.conn.execute(
            "SELECT timeout_minutes FROM guild_settings WHERE guild_id=?",
            (str(guild_id),),
        ) as cur:
            row = await cur.fetchone()
        return int(row[0]) if row else default

    async def set_timeout(self, guild_id: int, minutes: int):
        await self.conn.execute("""
            INSERT INTO guild_settings(guild_id, timeout_minutes)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                timeout_minutes=excluded.timeout_minutes
        """, (str(guild_id), minutes))
        await self.conn.commit()

    async def get_confirmation_messages(
        self, guild_id: int, default: bool = True
    ) -> bool:
        async with self.conn.execute(
            "SELECT confirmation_messages_enabled FROM guild_settings WHERE guild_id=?",
            (str(guild_id),),
        ) as cur:
            row = await cur.fetchone()
        return bool(row[0]) if row else default

    async def set_confirmation_messages(self, guild_id: int, enabled: bool):
        await self.conn.execute("""
            INSERT INTO guild_settings(
                guild_id, confirmation_messages_enabled
            )
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                confirmation_messages_enabled=excluded.confirmation_messages_enabled
        """, (str(guild_id), int(enabled)))
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()
