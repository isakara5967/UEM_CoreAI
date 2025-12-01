# UEM_CoreAI SQL DDL Files

**Version:** 2.0 (v5 - 16D StateVector Update)  
**Date:** 1 Aralık 2025

## 📁 Dosya Listesi

| Dosya | Açıklama | Çalıştırma Sırası |
|-------|----------|-------------------|
| `001_create_schema.sql` | Schema, extension, enum tanımları | 1️⃣ |
| `002_create_tables.sql` | Tüm tablo tanımları (public + core) | 2️⃣ |
| `003_create_indexes.sql` | Tüm index tanımları | 3️⃣ |
| `004_v5_migration_16d.sql` | v4→v5 migration (8D→16D) | 🔄 Migration |
| `005_seed_metric_registry.sql` | 52 PreData alan tanımları | 4️⃣ |

## 🚀 Kurulum (Yeni Veritabanı)

```bash
# PostgreSQL'e bağlan
psql -U uem -d uem_memory

# Scriptleri sırayla çalıştır
\i sql/001_create_schema.sql
\i sql/002_create_tables.sql
\i sql/003_create_indexes.sql
\i sql/005_seed_metric_registry.sql
```

## 🔄 Migration (v4 → v5)

Mevcut v4 veritabanını 16D'ye güncellemek için:

```bash
psql -U uem -d uem_memory -f sql/004_v5_migration_16d.sql
```

**⚠️ DİKKAT:** Migration öncesi backup alın!

```bash
pg_dump -U uem uem_memory > backup_v4.sql
```

## 📊 Tablo Özeti

### public Schema (Memory Storage - 16D)

| Tablo | Açıklama | 16D Kolonlar |
|-------|----------|--------------|
| `events` | Episodic Memory | state_before, effect, state_after |
| `snapshots` | State Snapshots | state_vector |

### core Schema (Logger/Analytics)

| Tablo | Açıklama |
|-------|----------|
| `experiments` | A/B test tanımları |
| `config_snapshots` | Konfigürasyon geçmişi |
| `modules` | Modül referansları |
| `submodules` | Alt modül referansları |
| `runs` | Çalıştırma oturumları |
| `cycles` | Cognitive cycle kayıtları |
| `events` | PreData payload (Logger) |
| `metamind_cycle_summary` | MetaMind analiz özeti |
| `alerts` | Sistem uyarıları |
| `metric_registry` | 52 PreData alan tanımları |

## 🔢 16D StateVector Yapısı

```
Index | Alan       | Tip     | Açıklama
------|------------|---------|------------------
0     | resource   | derived | (health + energy) / 2
1     | threat     | derived | danger_level
2     | wellbeing  | derived | (valence + 1) / 2
3     | health     | raw     | player_health
4     | energy     | raw     | player_energy
5     | valence    | raw     | emotion.valence
6     | arousal    | raw     | emotion.arousal
7     | dominance  | raw     | emotion.dominance
8-15  | reserved   | -       | Gelecek kullanım
```

## 📝 v5 Değişiklikler

### public.events
- ✅ `state_before vector(16)` eklendi
- ✅ `state_after vector(16)` eklendi
- ✅ `effect` 8D → 16D
- ❌ `emotion_valence` kaldırıldı
- ❌ `emotion_arousal` kaldırıldı

### public.snapshots
- ✅ `state_vector` 8D → 16D

## 🔧 Gereksinimler

- PostgreSQL 14+
- pgvector extension

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 📞 İletişim

Bu DDL dosyaları UEM_CoreAI PreData + Log sistemi için tasarlanmıştır.

**Hazırlayan:** Claude (Opus 4.5)  
**Tarih:** 1 Aralık 2025  
**Versiyon:** 2.0 (v5)
