// Estado da Aplicação
let currentAsset = 'CAT-797F-01';
let tempChart = null;
let pressureChart = null;

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    setupWebSocket();
});

// Alternar Visibilidade do Terminal CMD
function toggleTerminal() {
    const terminal = document.getElementById('cmdTerminal');
    terminal.classList.toggle('hidden');
    if (!terminal.classList.contains('hidden')) {
        document.getElementById('cmdInput').focus();
    }
}

// Seleção de Ativo
function selectAsset(assetId) {
    currentAsset = assetId;
    document.getElementById('selectedAssetTitle').innerText = `Ativo: ${assetId}`;
    
    document.querySelectorAll('.asset-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const activeItem = document.querySelector(`[onclick="selectAsset('${assetId}')"]`);
    if (activeItem) activeItem.classList.add('active');

    appendCmdOutput(`\n[SISTEMA] Ativo alterado para ${assetId}. Conectando telemetria...`, 'highlight');
}

// Lógica de Comandos do Terminal CMD
function handleCmdInput(event) {
    if (event.key === 'Enter') {
        const inputField = document.getElementById('cmdInput');
        const command = inputField.value.trim();
        
        if (command === '') return;

        // Adiciona linha do comando digitado
        appendCmdOutput(`C:\\Sotreq\\Diagnostics> ${command}`);
        inputField.value = '';

        // Executa processamento do comando
        processCommand(command.toLowerCase());
        
        // Auto-scroll para o final
        const cmdBody = document.getElementById('cmdBody');
        cmdBody.scrollTop = cmdBody.scrollHeight;
    }
}

function appendCmdOutput(text, className = '') {
    const cmdBody = document.getElementById('cmdBody');
    const p = document.createElement('p');
    p.className = `cmd-line ${className}`;
    p.innerText = text;
    cmdBody.appendChild(p);
}

function processCommand(cmd) {
    switch (cmd) {
        case 'help':
            appendCmdOutput('Comandos Disponíveis:');
            appendCmdOutput('  help           - Mostra esta lista de ajuda');
            appendCmdOutput('  ping           - Executa teste de conectividade com a máquina');
            appendCmdOutput('  status         - Exibe status da conexão e versão do software');
            appendCmdOutput('  clear          - Limpa o histórico do terminal');
            appendCmdOutput('  diag --quick   - Executa varredura rápida nos sensores ECM');
            break;
            
        case 'ping':
            appendCmdOutput(`Pinging ${currentAsset} [192.168.1.105] com 32 bytes de dados:`);
            setTimeout(() => appendCmdOutput('Resposta de 192.168.1.105: bytes=32 tempo=12ms TTL=64', 'success'), 300);
            setTimeout(() => appendCmdOutput('Resposta de 192.168.1.105: bytes=32 tempo=15ms TTL=64', 'success'), 600);
            setTimeout(() => appendCmdOutput('Estatísticas do Ping: Enviados = 2, Recebidos = 2, Perdidos = 0 (0% de perda)', 'highlight'), 900);
            break;

        case 'status':
            appendCmdOutput(`Status do Ativo: ${currentAsset}`);
            appendCmdOutput(`Conexão Telemetria: ONLINE`);
            appendCmdOutput(`Módulo ECM: V3.8.12-S11D`);
            break;

        case 'clear':
            document.getElementById('cmdBody').innerHTML = '';
            break;

        case 'diag --quick':
            appendCmdOutput('[DIAG] Iniciando diagnóstico de sensores...', 'highlight');
            setTimeout(() => appendCmdOutput(' - Sensor de Temp. Óleo: OK'), 400);
            setTimeout(() => appendCmdOutput(' - Sensor de Pressão Hidráulica: OK'), 800);
            setTimeout(() => appendCmdOutput(' - Módulo GNSS / Terrain: OK'), 1200);
            setTimeout(() => appendCmdOutput('[DIAG] Diagnóstico concluído. 0 falhas encontradas.', 'success'), 1500);
            break;

        default:
            appendCmdOutput(`'${cmd}' não é reconhecido como um comando interno. Digite 'help' para comandos.`, 'error');
            break;
    }
}

// Configuração e Inicialização dos Gráficos (Chart.js)
function initCharts() {
    const ctxTemp = document.getElementById('tempChart').getContext('2d');
    tempChart = new Chart(ctxTemp, {
        type: 'line',
        data: {
            labels: ['16:00', '16:05', '16:10', '16:15', '16:20', '16:25'],
            datasets: [{
                label: 'Temp (°C)',
                data: [82, 85, 84, 88, 89, 87],
                borderColor: '#FFCD00',
                backgroundColor: 'rgba(255, 205, 0, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#A0A0A0' }, grid: { color: '#333' } },
                y: { ticks: { color: '#A0A0A0' }, grid: { color: '#333' } }
            }
        }
    });

    const ctxPressure = document.getElementById('pressureChart').getContext('2d');
    pressureChart = new Chart(ctxPressure, {
        type: 'line',
        data: {
            labels: ['16:00', '16:05', '16:10', '16:15', '16:20', '16:25'],
            datasets: [{
                label: 'Pressão (PSI)',
                data: [2900, 2950, 2920, 3100, 3050, 3000],
                borderColor: '#2ECC71',
                backgroundColor: 'rgba(46, 204, 113, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#A0A0A0' }, grid: { color: '#333' } },
                y: { ticks: { color: '#A0A0A0' }, grid: { color: '#333' } }
            }
        }
    });
}

// Simulação de WebSocket / Telemetria
function setupWebSocket() {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    setTimeout(() => {
        if (statusDot && statusText) {
            statusDot.className = 'status-dot connected';
            statusText.innerText = 'Conectado (WS)';
        }
    }, 1000);
}

// Filtro de Ativos
function filterAssets() {
    const filter = document.getElementById('assetSearch').value.toLowerCase();
    const items = document.querySelectorAll('.asset-item');
    
    items.forEach(item => {
        const text = item.innerText.toLowerCase();
        item.style.display = text.includes(filter) ? 'flex' : 'none';
    });
}
