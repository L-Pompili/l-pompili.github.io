let session;
let stoi, itos, block_size, vocab_size;

ort.env.wasm.wasmPaths = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.20.0/dist/";

async function loadVocab() {
    try {
        const resp = await fetch("./vocab.json");
        const data = await resp.json();
        
        stoi = data.stoi;
        block_size = data.block_size;
        
        const rawItos = data.itos;
        vocab_size = Object.keys(rawItos).length;
        
        itos = new Array(vocab_size);
        for (let i = 0; i < vocab_size; i++) {
            itos[i] = rawItos[String(i)];
        }
        console.log("Vocab loaded. Size:", vocab_size);
    } catch (e) {
        console.error("Failed to load vocab.json", e);
    }
}

async function init() {
    await loadVocab();

    console.log("Loading ONNX model...");
    document.getElementById("output").textContent = "Loading model... (this might take a few seconds)";
    try {
        session = await ort.InferenceSession.create("./model_v3.onnx", {
            executionProviders: ["wasm"], 
        });
        
        console.log("Model loaded.");
        document.getElementById("output").textContent = "Model Ready! Type a prompt.";
    } catch (err) {
        console.error("Model Error:", err);
        document.getElementById("output").textContent = "Error: " + err.message;
    }
}

async function generate(start, T, temperature) {
    let x = [
        stoi["\n"],
        ...Array.from(start).map(c => stoi[c] ?? stoi[" "])
    ];
    for (let step = 0; step < T; step++) {
        let x_cond = x.slice(-block_size);

        const inputTensor = new ort.Tensor(
            "int64",
            BigInt64Array.from(x_cond.map(BigInt)),
            [1, x_cond.length]
        );

        const out = await session.run({ "input": inputTensor });
        const logits = out["output"].data;
        
        const startIdx = (x_cond.length - 1) * vocab_size;
        const lastLogits = logits.slice(startIdx, startIdx + vocab_size);

        const maxLogit = Math.max(...lastLogits);
        const exps = lastLogits.map(v => Math.exp((v - maxLogit) / temperature));
        const sumExp = exps.reduce((a, b) => a + b, 0);
        const probs = exps.map(v => v / sumExp);

        let r = Math.random();
        let cum = 0;
        let ix = vocab_size - 1;
        for (let i = 0; i < probs.length; i++) {
            cum += probs[i];
            if (r < cum) {
                ix = i;
                break;
            }
        }
        x.push(ix);
        
        if (step % 5 === 0) {
            await new Promise(r => setTimeout(r, 0));
            document.getElementById("output").textContent = x.slice(1).map(i => itos[i]).join("");
        }
    }
    let fullText = x.slice(1).map(i => itos[i]).join("");
    const lastDotIndex = fullText.lastIndexOf(".");
    if (lastDotIndex !== -1) {
        fullText = fullText.substring(0, lastDotIndex + 1);
    }
    document.getElementById("output").textContent = fullText;
    return fullText;
}

document.getElementById("generate").onclick = async () => {
    const prompt = document.getElementById("prompt").value;
    const temp = parseFloat(document.getElementById("temperature").value);
    document.getElementById("output").textContent = "Generating...";
    
    setTimeout(() => generate(prompt, 200, temp), 50);
};

document.getElementById("temperature").oninput = (e) => {
    document.getElementById("tempValue").textContent = e.target.value;
};

init();
