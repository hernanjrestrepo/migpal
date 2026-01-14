module.exports = {
  apps: [{
    name: 'migpal-bot',
    script: '/workspace/hjrm/migpal/backend/start_bot.sh',
    cwd: '/workspace/hjrm/migpal/backend',
    interpreter: '/bin/bash',
    watch: false,
    autorestart: true,
    max_restarts: 10,
    restart_delay: 5000,
    max_memory_restart: '500M',
    log_file: '/tmp/migpal_bot.log',
    out_file: '/tmp/migpal_bot.log',
    error_file: '/tmp/migpal_bot.log',
    merge_logs: true,
    time: true
  }]
};
