import { CRAWL_DEPTH_OPTIONS, SOURCE_TYPES, STORAGE_TYPES } from "../../constants/knowledgebase";
import type { SourceType, StorageType } from "../../types/knowledgebase";

export type KnowledgeBaseFormState = {
  storageType: StorageType | "";
  sourceType: SourceType;
  websiteUrl: string;
  crawlDepth: number;
  documentFile: File | null;
};

export const DEFAULT_KB_FORM_STATE: KnowledgeBaseFormState = {
  storageType: "",
  sourceType: "website",
  websiteUrl: "",
  crawlDepth: 2,
  documentFile: null,
};

export function isKnowledgeBaseFormValid(form: KnowledgeBaseFormState): boolean {
  if (!form.storageType) {
    return false;
  }
  if (form.sourceType === "website") {
    return form.websiteUrl.trim().length > 0;
  }
  return form.documentFile !== null;
}

type KnowledgeBaseFormFieldsProps = {
  form: KnowledgeBaseFormState;
  onChange: (next: KnowledgeBaseFormState) => void;
  compact?: boolean;
};

export function KnowledgeBaseFormFields({ form, onChange, compact = false }: KnowledgeBaseFormFieldsProps) {
  return (
    <div className="agent-form agent-form--compact">
      <div className="agent-form__section">
        <span className="agent-form__label">KNOWLEDGE BASE TYPE *</span>
        <div className={`kb-storage-grid ${compact ? "kb-storage-grid--compact" : ""}`}>
          {STORAGE_TYPES.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`kb-storage-card ${form.storageType === option.value ? "kb-storage-card--selected" : ""}`}
              onClick={() => onChange({ ...form, storageType: option.value })}
            >
              <span className="kb-storage-card__icon">{option.icon}</span>
              <strong>{option.label}</strong>
              {!compact ? <p>{option.description}</p> : null}
            </button>
          ))}
        </div>
      </div>

      <div className="agent-form__section">
        <span className="agent-form__label">CONTENT SOURCE *</span>
        <div className="kb-source-toggle">
          {SOURCE_TYPES.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`kb-source-toggle__btn ${form.sourceType === option.value ? "kb-source-toggle__btn--active" : ""}`}
              onClick={() =>
                onChange({
                  ...form,
                  sourceType: option.value,
                  websiteUrl: option.value === "website" ? form.websiteUrl : "",
                  documentFile: option.value === "file" ? form.documentFile : null,
                })
              }
            >
              {option.label}
            </button>
          ))}
        </div>
        <small>{SOURCE_TYPES.find((item) => item.value === form.sourceType)?.description}</small>
      </div>

      {form.sourceType === "website" ? (
        <>
          <label className="agent-form__field">
            <span>WEBSITE URL *</span>
            <input
              type="url"
              value={form.websiteUrl}
              onChange={(e) => onChange({ ...form, websiteUrl: e.target.value })}
              placeholder="https://www.yourcompany.com/help"
            />
          </label>
          <label className="agent-form__field">
            <span>CRAWL DEPTH *</span>
            <select
              value={form.crawlDepth}
              onChange={(e) => onChange({ ...form, crawlDepth: Number(e.target.value) })}
            >
              {CRAWL_DEPTH_OPTIONS.map((depth) => (
                <option key={depth} value={depth}>
                  {depth} {depth === 1 ? "level" : "levels"}
                </option>
              ))}
            </select>
          </label>
        </>
      ) : (
        <label className="agent-form__field">
          <span>DOCUMENT *</span>
          <input
            type="file"
            accept=".pdf,.docx,.txt,.md,.csv"
            onChange={(e) => onChange({ ...form, documentFile: e.target.files?.[0] ?? null })}
          />
          {form.documentFile ? <small>Selected: {form.documentFile.name}</small> : null}
        </label>
      )}
    </div>
  );
}
