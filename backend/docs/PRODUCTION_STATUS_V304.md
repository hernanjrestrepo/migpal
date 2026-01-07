# 🟢 MigPAL Production Status v3.0.4

**Última actualización:** 2026-01-07 08:33 UTC
**Versión:** v3.0.4
**Estado:** ✅ ESTABLE - MODO OBSERVACIÓN

---

## 📊 Estado Actual

| Componente | Estado |
|------------|--------|
| Bot | ✅ Corriendo (PID: 153634) |
| Polling | ✅ Activo (~10s) |
| Errores | ✅ 0 |
| Usuarios Activos | ✅ Sí |

---

## 🔍 Monitoreo Activo

### Scripts Disponibles

```bash
# Verificar estado
./scripts/cron_monitor.sh status

# Verificar errores
./scripts/cron_monitor.sh check

# Generar métricas
./scripts/cron_monitor.sh metrics

# Monitoreo continuo
./scripts/cron_monitor.sh watch
```

### Crontab Sugerido

```cron
# Verificar errores cada 5 minutos
*/5 * * * * /workspace/hjrm/migpal/backend/scripts/cron_monitor.sh check >> /workspace/hjrm/migpal/backend/logs/monitor.log 2>&1

# Generar métricas diarias a medianoche
0 0 * * * /workspace/hjrm/migpal/backend/scripts/cron_monitor.sh metrics >> /workspace/hjrm/migpal/backend/logs/monitor.log 2>&1
```

---

## 📈 Métricas Beta

### Ubicación
- Snapshots: `/workspace/hjrm/migpal/backend/data/beta_metrics/`
- Alertas: `/workspace/hjrm/migpal/backend/data/alerts.jsonl`

### Métricas Rastreadas
- Tiempo por fase
- Abandonos por fase
- Repetición de mensajes
- Indicadores de frustración
- Tasa de conversión

---

## 🚨 Protocolo de Incidentes

### Si aparece un ERROR:

1. **Capturar contexto:**
   ```bash
   grep -B5 -A10 "ERROR" logs/bot_v3.log | tail -50
   ```

2. **Identificar:**
   - User ID
   - State/Phase
   - Locale
   - Intent
   - Stacktrace completo

3. **Congelar beta si es crítico:**
   ```bash
   tmux send-keys -t migpal_bot C-c
   ```

4. **Hotfix:**
   - Crear test que reproduzca el bug
   - Aplicar fix mínimo
   - Ejecutar tests
   - Reiniciar bot

5. **Documentar:**
   - Agregar a alerts.jsonl
   - Actualizar este documento

---

## 📋 Historial de Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| v3.0.4 | 2026-01-07 | Fix TypeError en flow_pref_tech |
| v3.0.3 | 2026-01-07 | UX Improvements (7 mejoras) |
| v3.0.2 | 2026-01-07 | Fix NameError en FORM_STATES |
| v3.0.1 | 2026-01-07 | Hotfix i18n + UX nombre |

---

## 🔒 Reglas de Producción

1. **NO agregar features** - Solo hotfixes críticos
2. **Monitoreo continuo** - Verificar errores cada 5 min
3. **Métricas diarias** - Snapshot a medianoche
4. **Hotfix inmediato** - Si aparece crash o fallback genérico
5. **Test por bug** - Cada fix debe tener test

---

## 📞 Comandos Útiles

```bash
# Ver logs en tiempo real
tail -f /workspace/hjrm/migpal/backend/logs/bot_v3.log

# Buscar errores
grep -E 'ERROR|Exception' logs/bot_v3.log

# Ver actividad de usuarios
grep -E 'MSG:|CB:' logs/bot_v3.log | tail -20

# Reiniciar bot
tmux send-keys -t migpal_bot C-c
sleep 2
tmux send-keys -t migpal_bot 'source .venv/bin/activate && python run_telegram_bot.py 2>&1 | tee logs/bot_v3.log' Enter

# Ejecutar tests
python -m pytest tests/ -v
```

---

## ✅ Checklist Diario

- [ ] Verificar que el bot está corriendo
- [ ] Revisar logs por errores
- [ ] Generar snapshot de métricas
- [ ] Revisar alertas pendientes
- [ ] Documentar cualquier incidente

---

*Documento generado automáticamente - 2026-01-07*
