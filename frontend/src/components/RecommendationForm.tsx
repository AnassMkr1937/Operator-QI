import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import type {
  CandidateOperator,
  RecommendationRequest,
  RequiredSkill,
  Shift,
} from "../types/recommendation";

interface SkillRow extends RequiredSkill {
  _key: string;
}

interface FormValues {
  operation_id: string;
  name: string;
  assignment_date: string;
  shift: Shift;
  category: string;
  top_n: string;
  required_skills: SkillRow[];
  candidates_json: string;
}

interface FormErrors {
  operation_id?: string;
  name?: string;
  assignment_date?: string;
  candidates_json?: string;
  top_n?: string;
}

interface Props {
  onSubmit: (request: RecommendationRequest) => void;
  isLoading: boolean;
}

const CANDIDATE_PLACEHOLDER = JSON.stringify(
  [
    {
      operator_id: "OP-A",
      name: "Alice Martin",
      is_active: true,
      skills: [
        {
          skill_id: "welding",
          proficiency: 4,
          certified: true,
          last_used_date: "2024-06-01",
        },
      ],
      assignments: [],
    },
    {
      operator_id: "OP-B",
      name: "Bob Dupont",
      is_active: true,
      skills: [{ skill_id: "welding", proficiency: 2, certified: false }],
      assignments: [],
    },
  ],
  null,
  2,
);

function makeKey(): string {
  return `${Date.now()}-${Math.random()}`;
}

function makeEmptySkill(): SkillRow {
  return { _key: makeKey(), skill_id: "", min_proficiency: 1, mandatory: true };
}

const DEFAULT_VALUES: FormValues = {
  operation_id: "",
  name: "",
  assignment_date: "",
  shift: "morning",
  category: "",
  top_n: "5",
  required_skills: [makeEmptySkill()],
  candidates_json: "",
};

export default function RecommendationForm({ onSubmit, isLoading }: Props) {
  const [values, setValues] = useState<FormValues>(DEFAULT_VALUES);
  const [errors, setErrors] = useState<FormErrors>({});

  function setField<K extends keyof FormValues>(key: K, val: FormValues[K]) {
    setValues((v) => ({ ...v, [key]: val }));
    if (key in errors) setErrors((e) => ({ ...e, [key]: undefined }));
  }

  function handleText(
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) {
    setField(e.target.name as keyof FormValues, e.target.value as never);
  }

  // ----- required skills -----
  function addSkill() {
    setValues((v) => ({
      ...v,
      required_skills: [...v.required_skills, makeEmptySkill()],
    }));
  }

  function removeSkill(key: string) {
    setValues((v) => ({
      ...v,
      required_skills: v.required_skills.filter((s) => s._key !== key),
    }));
  }

  function updateSkill(key: string, patch: Partial<RequiredSkill>) {
    setValues((v) => ({
      ...v,
      required_skills: v.required_skills.map((s) =>
        s._key === key ? { ...s, ...patch } : s,
      ),
    }));
  }

  // ----- validation -----
  function validate(): boolean {
    const errs: FormErrors = {};

    if (!values.operation_id.trim())
      errs.operation_id = "L'identifiant d'opération est requis.";
    if (!values.name.trim()) errs.name = "Le nom de l'opération est requis.";
    if (!values.assignment_date)
      errs.assignment_date = "La date d'affectation est requise.";

    const topN = Number(values.top_n);
    if (!values.top_n || isNaN(topN) || topN < 1 || topN > 100)
      errs.top_n = "top_n doit être entre 1 et 100.";

    if (!values.candidates_json.trim()) {
      errs.candidates_json = "Au moins un candidat JSON est requis.";
    } else {
      try {
        const parsed = JSON.parse(values.candidates_json) as unknown;
        if (!Array.isArray(parsed) || parsed.length === 0)
          errs.candidates_json =
            "Les candidats doivent être un tableau JSON non vide.";
      } catch {
        errs.candidates_json = "JSON invalide pour les candidats.";
      }
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    const candidates = JSON.parse(
      values.candidates_json,
    ) as CandidateOperator[];

    const request: RecommendationRequest = {
      operation: {
        operation_id: values.operation_id.trim(),
        name: values.name.trim(),
        required_skills: values.required_skills
          .filter((s) => s.skill_id.trim() !== "")
          .map(({ _key: _k, ...rest }) => rest),
        assignment_date: values.assignment_date,
        shift: values.shift,
        category: values.category.trim() || undefined,
      },
      candidates,
      top_n: Number(values.top_n),
    };

    onSubmit(request);
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="rec-form">
      <h2 className="rec-form__title">Recommandation d&apos;opérateurs</h2>

      {/* Operation section */}
      <fieldset className="rec-form__fieldset">
        <legend>Contexte de l&apos;opération</legend>

        <div className="rec-form__row">
          <label htmlFor="operation_id">
            Identifiant *
            <input
              id="operation_id"
              name="operation_id"
              value={values.operation_id}
              onChange={handleText}
              placeholder="OP-001"
              aria-describedby={
                errors.operation_id ? "err-operation_id" : undefined
              }
            />
          </label>
          {errors.operation_id && (
            <span id="err-operation_id" className="rec-form__error" role="alert">
              {errors.operation_id}
            </span>
          )}
        </div>

        <div className="rec-form__row">
          <label htmlFor="name">
            Nom de l&apos;opération *
            <input
              id="name"
              name="name"
              value={values.name}
              onChange={handleText}
              placeholder="Ligne d'assemblage A"
              aria-describedby={errors.name ? "err-name" : undefined}
            />
          </label>
          {errors.name && (
            <span id="err-name" className="rec-form__error" role="alert">
              {errors.name}
            </span>
          )}
        </div>

        <div className="rec-form__row rec-form__row--inline">
          <label htmlFor="assignment_date">
            Date d&apos;affectation *
            <input
              id="assignment_date"
              type="date"
              name="assignment_date"
              value={values.assignment_date}
              onChange={handleText}
              aria-describedby={
                errors.assignment_date ? "err-assignment_date" : undefined
              }
            />
          </label>
          {errors.assignment_date && (
            <span
              id="err-assignment_date"
              className="rec-form__error"
              role="alert"
            >
              {errors.assignment_date}
            </span>
          )}

          <label htmlFor="shift">
            Vacation
            <select
              id="shift"
              name="shift"
              value={values.shift}
              onChange={handleText}
            >
              <option value="morning">Matin</option>
              <option value="afternoon">Après-midi</option>
              <option value="night">Nuit</option>
            </select>
          </label>

          <label htmlFor="category">
            Catégorie
            <input
              id="category"
              name="category"
              value={values.category}
              onChange={handleText}
              placeholder="assemblage"
            />
          </label>

          <label htmlFor="top_n">
            Top-N *
            <input
              id="top_n"
              type="number"
              name="top_n"
              value={values.top_n}
              onChange={handleText}
              min={1}
              max={100}
              aria-describedby={errors.top_n ? "err-top_n" : undefined}
            />
          </label>
          {errors.top_n && (
            <span id="err-top_n" className="rec-form__error" role="alert">
              {errors.top_n}
            </span>
          )}
        </div>
      </fieldset>

      {/* Required skills */}
      <fieldset className="rec-form__fieldset">
        <legend>Compétences requises</legend>
        {values.required_skills.map((skill) => (
          <div key={skill._key} className="rec-form__skill-row">
            <input
              aria-label="Identifiant compétence"
              placeholder="ex: welding"
              value={skill.skill_id}
              onChange={(e) =>
                updateSkill(skill._key, { skill_id: e.target.value })
              }
            />
            <label className="rec-form__inline-label">
              Niveau min
              <select
                aria-label="Niveau min"
                value={skill.min_proficiency}
                onChange={(e) =>
                  updateSkill(skill._key, {
                    min_proficiency: Number(e.target.value),
                  })
                }
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
            <label className="rec-form__inline-label">
              <input
                type="checkbox"
                aria-label="Obligatoire"
                checked={skill.mandatory}
                onChange={(e) =>
                  updateSkill(skill._key, { mandatory: e.target.checked })
                }
              />
              Obligatoire
            </label>
            <button
              type="button"
              className="rec-form__btn-remove"
              onClick={() => removeSkill(skill._key)}
              disabled={values.required_skills.length === 1}
              aria-label="Supprimer la compétence"
            >
              ✕
            </button>
          </div>
        ))}
        <button type="button" className="rec-form__btn-add" onClick={addSkill}>
          + Ajouter une compétence
        </button>
      </fieldset>

      {/* Candidates JSON */}
      <fieldset className="rec-form__fieldset">
        <legend>Candidats (JSON)</legend>
        <p className="rec-form__hint">
          Collez un tableau JSON de candidats. Chaque entrée doit contenir{" "}
          <code>operator_id</code>, <code>name</code>, <code>is_active</code>,{" "}
          <code>skills</code> et <code>assignments</code>.
        </p>
        <textarea
          id="candidates_json"
          name="candidates_json"
          rows={10}
          value={values.candidates_json}
          onChange={handleText}
          placeholder={CANDIDATE_PLACEHOLDER}
          aria-label="Candidats JSON"
          aria-describedby={
            errors.candidates_json ? "err-candidates_json" : undefined
          }
        />
        {errors.candidates_json && (
          <span
            id="err-candidates_json"
            className="rec-form__error"
            role="alert"
          >
            {errors.candidates_json}
          </span>
        )}
        <button
          type="button"
          className="rec-form__btn-add"
          onClick={() => setField("candidates_json", CANDIDATE_PLACEHOLDER)}
        >
          Charger l&apos;exemple
        </button>
      </fieldset>

      <button
        type="submit"
        className="rec-form__btn-submit"
        disabled={isLoading}
      >
        {isLoading ? "Chargement…" : "Obtenir les recommandations"}
      </button>
    </form>
  );
}
