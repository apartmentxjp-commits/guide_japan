# Runbook: Troubleshooting

## Quick Diagnostics

```bash
# 1. Are containers running?
docker-compose ps

# 2. Check backend health
curl http://localhost:8000/api/health

# 3. Check recent logs
docker logs guide-japan-backend --tail 50
docker logs guide-japan-scheduler --tail 50

# 4. Check GitHub Actions
# → https://github.com/apartmentxjp-commits/guide_japan/actions
```

---

## Common Issues

### Issue: No articles being generated

**Symptoms**: Scheduler logs show "Skipping — no topics in queue"

**Fix**:
```bash
python tools/scripts/openclaw-runner.py --add-topics
docker restart guide-japan-scheduler
```

---

### Issue: Articles generated but not appearing on site

**Symptoms**: Publisher log shows "GitHub API push success" but site not updated.

**Check**:
1. Go to https://github.com/apartmentxjp-commits/guide_japan/actions
2. Confirm GitHub Actions ran successfully
3. Check Actions for Hugo build errors

**Common cause**: Hugo front matter syntax error in generated article.

**Fix**:
```bash
# Find the bad article
cd site && hugo --verbose 2>&1 | grep -i error

# Fix front matter
nano site/content/{category}/{slug}.md
```

---

### Issue: AI returns gibberish or wrong language

**Symptoms**: Article contains non-English text or is nonsensical.

**Fix**:
```bash
# Check which model was used
grep "model=" logs/writer.log | tail -20

# Force use of better model
FORCE_MODEL=anthropic/claude-3.5-sonnet python tools/scripts/openclaw-runner.py --retry {slug}
```

---

### Issue: GitHub API returns 401 Unauthorized

**Symptoms**: `[Publisher] GitHub API error: 401`

**Fix**:
1. Check `GH_TOKEN` in `.env`
2. Verify token has `repo` scope at https://github.com/settings/tokens
3. Regenerate token if expired

---

### Issue: Docker containers not starting

```bash
# Check docker-compose config
docker-compose config

# Rebuild containers
docker-compose down && docker-compose build && docker-compose up -d

# Check env file
cat .env | grep -v "KEY\|TOKEN"  # don't expose secrets
```

---

### Issue: Duplicate articles being published

**Symptoms**: Same slug appears twice in site/content/

**Fix**:
```bash
python tools/scripts/dedupe.py --fix
```
This scans all slugs, finds duplicates, and removes the older one.

---

## Emergency: Pause article generation

```bash
# Stop scheduler without stopping backend
docker stop guide-japan-scheduler

# Restart when ready
docker start guide-japan-scheduler
```

---

## Reset article queue

```bash
python tools/scripts/openclaw-runner.py --reset-queue
python tools/scripts/openclaw-runner.py --add-topics
```
