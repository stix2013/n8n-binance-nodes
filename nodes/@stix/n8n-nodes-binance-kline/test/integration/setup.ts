import express from 'express';
import { Server } from 'http';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import getPort from 'get-port';
import treeKill from 'tree-kill';
import axios from 'axios';

// Global state
export let apiPort: number;
export let mockBinancePort: number;
let apiProcess: ChildProcess;
let mockServer: Server;

interface MockResponse {
    method: string;
    path: string | RegExp;
    statusCode: number;
    body: any;
}

const mockResponses: MockResponse[] = [];
const requestLog: any[] = [];

export const mockBinance = {
    add: (method: string, path: string | RegExp, statusCode: number, body: any) => {
        mockResponses.push({ method, path, statusCode, body });
    },
    clear: () => {
        mockResponses.length = 0;
        requestLog.length = 0;
    },
    getRequests: () => requestLog,
};

const startMockServer = async () => {
    mockBinancePort = await getPort();
    const app = express();
    app.use(express.json());

    // Catch-all handler
    app.use((req, res) => {
        const method = req.method;
        const path = req.path;
        
        requestLog.push({ 
            method, 
            path, 
            query: req.query, 
            body: req.body, 
            headers: req.headers 
        });

        // Find matching mock (LIFO or FIFO? Let's do First Match)
        const mock = mockResponses.find(m => 
            m.method === method && (typeof m.path === 'string' ? m.path === path : m.path.test(path))
        );

        if (mock) {
            // console.log(`[MockBinance] Matched ${method} ${path}`);
            res.status(mock.statusCode).json(mock.body);
            return;
        }

        console.warn(`[MockBinance] Unmatched Request: ${method} ${path}`);
        res.status(404).json({ msg: 'Mock not found', path });
    });

    return new Promise<void>((resolve) => {
        mockServer = app.listen(mockBinancePort, () => {
            console.log(`[MockBinance] Listening on port ${mockBinancePort}`);
            resolve();
        });
    });
};

const startBackend = async () => {
    apiPort = await getPort();
    
    // Resolve project root from: nodes/@stix/n8n-nodes-binance-kline/test/integration/setup.ts
    const projectRoot = path.resolve(__dirname, '../../../../../');
    const apiDir = path.join(projectRoot, 'api');
    const venvBin = path.join(apiDir, '.venv/bin');
    
    // Ensure venv exists
    const fs = require('fs');
    if (!fs.existsSync(venvBin)) {
        throw new Error(`Virtual environment not found at ${venvBin}. Please run 'bun install' or setup python env.`);
    }

    const env = {
        ...process.env,
        API_PORT: apiPort.toString(),
        BINANCE_BASE_URL: `http://127.0.0.1:${mockBinancePort}`,
        BINANCE_API_KEY: 'test_key',
        BINANCE_SECRET_KEY: 'test_secret',
        PYTHONPATH: path.join(apiDir, 'src'), // Add src to python path explicitly
        API_LOG_LEVEL: 'DEBUG'
    };

    console.log(`[Setup] Starting FastAPI on port ${apiPort} with Binance Mock at ${mockBinancePort}`);

    apiProcess = spawn(
        path.join(venvBin, 'uvicorn'),
        ['src.main:app', '--host', '127.0.0.1', '--port', apiPort.toString()],
        {
            cwd: apiDir,
            env,
            // stdio: 'inherit', // Uncomment to see API logs in test output
        }
    );

    // Wait for health check
    let attempts = 0;
    while (attempts < 30) {
        try {
            await axios.get(`http://127.0.0.1:${apiPort}/health`);
            console.log('[Setup] FastAPI is ready');
            return;
        } catch (e) {
            await new Promise(r => setTimeout(r, 1000));
            attempts++;
        }
    }
    
    // If we fail, kill the process and throw
    if (apiProcess.pid) treeKill(apiProcess.pid, 'SIGKILL');
    throw new Error('FastAPI failed to start within 30 seconds');
};

export const setupTestEnvironment = async () => {
    await startMockServer();
    await startBackend();
    process.env.N8N_BINANCE_API_URL = `http://127.0.0.1:${apiPort}`;
};

export const teardownTestEnvironment = async () => {
    if (apiProcess && apiProcess.pid) {
        await new Promise<void>(resolve => treeKill(apiProcess.pid!, 'SIGTERM', (err) => resolve()));
    }
    if (mockServer) {
        mockServer.close();
    }
};
