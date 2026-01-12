# Dang Dang AI - PostgreSQL Migration Setup Guide

## 🎯 Quick Start

### Prerequisites
- Python 3.10+
- Docker Desktop installed and running
- Existing `.env` file with API keys

### Step 1: Update Environment Variables

Add these lines to your `.env` file:

```bash
# PostgreSQL Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dangdang_db
DB_USER=dangdang
DB_PASSWORD=<your-secure-password-here>
```

**⚠️ Important**: Replace `<your-secure-password-here>` with a strong password!

---

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `psycopg2-binary` (PostgreSQL adapter) and other dependencies.

---

### Step 3: Start PostgreSQL Container

```bash
docker-compose up -d
```

**Verify it's running:**
```bash
docker-compose ps
```

You should see:
```
NAME                  STATUS
dangdang_postgres     Up (healthy)
```

---

### Step 4: Run Migration

```bash
python migrate_sqlite_to_postgres.py
```

This will:
1. ✅ Backup your existing SQLite database (if it exists)
2. ✅ Create PostgreSQL schema
3. ✅ Migrate all data
4. ✅ Verify migration success

**Expected output:**
```
✅ SQLite backup created: dangdang_memory_backup_20260112_182345.db
✅ Connected to PostgreSQL
📝 Creating PostgreSQL schema...
✅ PostgreSQL schema created with indices
📦 Migrating bot_state... ✅ 1 rows
📦 Migrating messages... ✅ 15 rows
...
🎉 MIGRATION SUCCESSFUL!
```

---

### Step 5: Run Application

```bash
python main.py
```

You're done! 🎉

---

## 🛠️ Troubleshooting

### Problem: "Failed to connect to PostgreSQL"

**Solution:**
1. Check Docker container status:
   ```bash
   docker-compose ps
   ```
2. View logs:
   ```bash
   docker-compose logs postgres
   ```
3. Verify `.env` has correct `DB_PASSWORD`

---

### Problem: "Database connection pool initialization failed"

**Solution:**
1. Restart PostgreSQL container:
   ```bash
   docker-compose restart
   ```
2. Wait 10 seconds for health check to pass
3. Try again

---

### Problem: Migration shows "database locked"

**Solution:**
1. Stop main.py if running
2. Delete `dangdang_memory.db-journal` if it exists
3. Run migration again

---

## 📋 Useful Commands

```bash
# View PostgreSQL logs
docker-compose logs -f postgres

# Stop PostgreSQL
docker-compose down

# Restart PostgreSQL (if issues)
docker-compose restart

# Connect to PostgreSQL directly (for debugging)
docker-compose exec postgres psql -U dangdang -d dangdang_db

# Backup database manually
docker-compose exec postgres pg_dump -U dangdang dangdang_db > backup.sql

# View database size
docker-compose exec postgres psql -U dangdang -d dangdang_db -c "SELECT pg_size_pretty(pg_database_size('dangdang_db'));"
```

---

## 🔄 Rollback to SQLite (If Needed)

If you encounter issues and want to rollback:

1. Stop application
2. Restore SQLite backup:
   ```bash
   cp dangdang_memory_backup_<timestamp>.db dangdang_memory.db
   ```
3. Checkout old code version that used SQLite
4. Run with SQLite version

---

## 📊 What Changed?

| Component | Old (SQLite) | New (PostgreSQL) |
|-----------|--------------|------------------|
| **Database** | SQLite file | Docker PostgreSQL container |
| **Threading** | DatabaseWorker workaround | Native connection pooling |
| **Syntax** | `?` placeholders | `%s` placeholders |
| **Data types** | `INTEGER`, `REAL` | `SERIAL`, `NUMERIC` |
| **Backup** | Copy `.db` file | `pg_dump` command |

---

## ✅ Health Check

To verify everything is working:

```bash
# Test database connection
python -c "from memory import MemoryManager; m = MemoryManager(); print('✅ OK')"

# Check bot state
python -c "from memory import MemoryManager; m = MemoryManager(); print(m.get_bot_state())"
```

---

## 🎓 Next Steps

Now that PostgreSQL is setup, you can:

1. **Phase 2**: Add logging system and guardrails
2. **Phase 3**: Implement enhanced memory decay
3. **Future**: Use pgvector for semantic search
