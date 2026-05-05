"use client";

interface ModelSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

export function ModelSelector({ value, onChange }: ModelSelectorProps) {
  return (
    <div>
      <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Model</label>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-800 shadow-sm"
      >
        <option value="segformer">SegFormer-B2 ADE20K free</option>
        <option value="gpt-4o-mini">GPT-4o-mini optional API key</option>
        <option value="gpt-4.1-mini">gpt-4.1-mini optional API key</option>
      </select>
      <p className="mt-1 text-xs text-slate-500">GPT options require server-side ENABLE_LLM=true and OPENAI_API_KEY. The free SegFormer option does not need any API key.</p>
    </div>
  );
}
