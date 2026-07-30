import type { ExecutorCatalogItem } from "../../types/executor";

type ToolConfigFieldsProps = {
  executor: ExecutorCatalogItem;
  values: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
};

function fieldLabel(key: string, required?: boolean): string {
  const label = key.replace(/_/g, " ").toUpperCase();
  return required ? `${label} *` : label;
}

export function parseToolConfig(
  executor: ExecutorCatalogItem,
  values: Record<string, string>,
): { config: Record<string, unknown> | null; error: string | null } {
  const config: Record<string, unknown> = {};

  for (const [key, schema] of Object.entries(executor.config_schema)) {
    const raw = values[key]?.trim() ?? "";

    if (!raw) {
      if (schema.required) {
        return { config: null, error: `${key} is required.` };
      }
      continue;
    }

    if (schema.type === "string" || schema.type === "enum") {
      config[key] = raw;
      continue;
    }

    if (schema.type === "integer") {
      const parsed = Number(raw);
      if (!Number.isInteger(parsed)) {
        return { config: null, error: `${key} must be an integer.` };
      }
      config[key] = parsed;
      continue;
    }

    if (schema.type === "object" || schema.type === "array") {
      try {
        config[key] = JSON.parse(raw);
      } catch {
        return { config: null, error: `${key} must be valid JSON.` };
      }
      if (schema.type === "object" && (config[key] === null || Array.isArray(config[key]))) {
        return { config: null, error: `${key} must be a JSON object.` };
      }
      if (schema.type === "array" && !Array.isArray(config[key])) {
        return { config: null, error: `${key} must be a JSON array.` };
      }
    }
  }

  return { config, error: null };
}

export function isToolConfigValid(executor: ExecutorCatalogItem, values: Record<string, string>): boolean {
  return parseToolConfig(executor, values).error === null;
}

export function defaultConfigValues(executor: ExecutorCatalogItem): Record<string, string> {
  const values: Record<string, string> = {};
  for (const [key, schema] of Object.entries(executor.config_schema)) {
    if (schema.type === "enum" && schema.values?.length) {
      values[key] = schema.values[0];
    } else {
      values[key] = "";
    }
  }
  return values;
}

export function ToolConfigFields({ executor, values, onChange }: ToolConfigFieldsProps) {
  return (
    <div className="agent-form agent-form--compact">
      {Object.entries(executor.config_schema).map(([key, schema]) => {
        const value = values[key] ?? "";

        if (schema.type === "enum" && schema.values) {
          return (
            <label key={key} className="agent-form__field">
              <span>{fieldLabel(key, schema.required)}</span>
              <select
                value={value}
                onChange={(e) => onChange({ ...values, [key]: e.target.value })}
              >
                {schema.values.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
          );
        }

        if (schema.type === "object" || schema.type === "array") {
          return (
            <label key={key} className="agent-form__field">
              <span>{fieldLabel(key, schema.required)}</span>
              <textarea
                rows={4}
                value={value}
                placeholder={schema.type === "array" ? '["stage1", "stage2"]' : '{"field": "{{arg}}"}'}
                onChange={(e) => onChange({ ...values, [key]: e.target.value })}
              />
              <small>Use {"{{arg_name}}"} for runtime arguments from the LLM.</small>
            </label>
          );
        }

        return (
          <label key={key} className="agent-form__field">
            <span>{fieldLabel(key, schema.required)}</span>
            <input
              type={schema.type === "integer" ? "number" : "text"}
              value={value}
              onChange={(e) => onChange({ ...values, [key]: e.target.value })}
            />
          </label>
        );
      })}
    </div>
  );
}
