import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { Check, ChevronLeft, ChevronRight, Lock } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { Assessment } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Error } from "@/pages/AuthPages";

const get = <T,>(path: string) => async () => (await api.get<T>(path)).data;

/**
 * The six dimensions the assessments API accepts. These map 1:1 to
 * AssessmentScore.Dimension on the backend — adding one here without a matching
 * backend choice will be rejected by the serializer.
 */
const DIMENSIONS = [
  { key: "quantitative", title: "Quantitative aptitude", blurb: "Arithmetic, data interpretation, and numerical reasoning under time pressure." },
  { key: "logical", title: "Logical reasoning", blurb: "Pattern recognition, deductions, and puzzle-style problem solving." },
  { key: "coding", title: "Coding & problem solving", blurb: "Data structures, algorithms, and translating a problem into working code." },
  { key: "communication", title: "Communication", blurb: "Written clarity, spoken fluency, and structuring an explanation." },
  { key: "interview", title: "Technical interview", blurb: "Explaining trade-offs, system design discussion, and thinking aloud." },
  { key: "presentation", title: "Presentation", blurb: "Slide structure, delivery, and defending your work to a panel." },
] as const;

type Scores = Record<string, number>;

const BANDS = [
  { min: 85, label: "Strong", tone: "text-emerald-700" },
  { min: 70, label: "Competent", tone: "text-emerald-700" },
  { min: 55, label: "Developing", tone: "text-amber-700" },
  { min: 40, label: "Needs work", tone: "text-amber-700" },
  { min: 0, label: "Priority gap", tone: "text-rose-700" },
];

const bandFor = (value: number) => BANDS.find((b) => value >= b.min)!;

function Stepper({ index, completed }: { index: number; completed: Set<number> }) {
  return (
    <ol className="flex flex-wrap gap-2">
      {DIMENSIONS.map((dimension, position) => {
        const state = position === index ? "current" : completed.has(position) ? "done" : "todo";
        const tone =
          state === "current" ? "border-indigo-600 bg-indigo-50 text-indigo-700"
          : state === "done" ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-slate-200 bg-white text-slate-400";
        return (
          <li key={dimension.key} className={`flex items-center gap-2 rounded-md border px-3 py-1.5 text-xs ${tone}`}>
            <span className="flex h-5 w-5 items-center justify-center rounded-full border text-[11px]">
              {state === "done" ? <Check className="h-3 w-3" /> : position + 1}
            </span>
            {dimension.title}
          </li>
        );
      })}
    </ol>
  );
}

export function AssessmentPage() {
  const cache = useQueryClient();
  const navigate = useNavigate();
  const [index, setIndex] = useState(0);
  const [scores, setScores] = useState<Scores>({});
  const [error, setError] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const history = useQuery({ queryKey: ["assessments"], queryFn: get<{ results: Assessment[] }>("/v1/assessments/") });

  const submit = useMutation({
    mutationFn: async (body: { recalculate: boolean }) => {
      await api.post("/v1/assessments/", {
        type: "diagnostic",
        scores: Object.entries(scores).map(([dimension, score]) => ({ dimension, score, max_score: 100 })),
      });
      if (body.recalculate) await api.post("/v1/predictions/", {});
    },
    onSuccess: () => {
      void cache.invalidateQueries({ queryKey: ["assessments"] });
      void cache.invalidateQueries({ queryKey: ["prediction"] });
      void cache.invalidateQueries({ queryKey: ["profile"] });
      navigate("/student");
    },
    onError: (e) => setError(errorMessage(e)),
  });

  const current = DIMENSIONS[index];
  const answered = new Set(DIMENSIONS.map((d, i) => (scores[d.key] === undefined ? -1 : i)).filter((i) => i >= 0));
  const value = scores[current.key];
  const setValue = (next: number) => setScores((prior) => ({ ...prior, [current.key]: next }));

  if (reviewing) {
    const entries = DIMENSIONS.filter((d) => scores[d.key] !== undefined);
    return (
      <section className="space-y-6">
        <div>
          <p className="text-sm font-medium text-indigo-600">Diagnostic assessment</p>
          <h1 className="text-3xl font-bold">Review &amp; submit</h1>
        </div>
        {error && <Error text={error} />}
        <section className="rounded-lg border bg-white p-5">
          <ul className="space-y-3">
            {entries.map((dimension) => {
              const score = scores[dimension.key];
              const band = bandFor(score);
              return (
                <li key={dimension.key}>
                  <div className="flex items-baseline justify-between text-sm">
                    <span className="text-slate-700">{dimension.title}</span>
                    <span className="font-semibold text-slate-900">
                      {score}<span className="font-normal text-slate-400"> / 100</span>
                      <span className={`ml-2 text-xs ${band.tone}`}>{band.label}</span>
                    </span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-indigo-500" style={{ width: `${score}%` }} />
                  </div>
                </li>
              );
            })}
          </ul>
          <p className="mt-4 text-sm text-slate-500">
            Submitting records one diagnostic assessment with {entries.length} dimension score
            {entries.length === 1 ? "" : "s"}. Scores feed the readiness model as assessment-verified inputs.
          </p>
        </section>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => setReviewing(false)}>
            <ChevronLeft className="mr-2 h-4 w-4" />Back to questions
          </Button>
          <Button variant="outline" onClick={() => submit.mutate({ recalculate: false })} disabled={submit.isPending}>
            {submit.isPending ? "Submitting…" : "Submit only"}
          </Button>
          <Button onClick={() => submit.mutate({ recalculate: true })} disabled={submit.isPending}>
            {submit.isPending ? "Submitting…" : "Submit & recalculate readiness"}
          </Button>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-medium text-indigo-600">Diagnostic assessment</p>
        <h1 className="text-3xl font-bold">Step {index + 1} of {DIMENSIONS.length}: {current.title}</h1>
      </div>

      {error && <Error text={error} />}

      <Stepper index={index} completed={answered} />

      <div className="h-1.5 rounded-full bg-slate-100">
        <div className="h-1.5 rounded-full bg-indigo-600 transition-[width] duration-300" style={{ width: `${(answered.size / DIMENSIONS.length) * 100}%` }} />
      </div>

      <section className="rounded-lg border bg-white p-5">
        <h2 className="font-semibold text-slate-900">{current.title}</h2>
        <p className="mt-1 text-sm text-slate-500">{current.blurb}</p>

        <label className="mt-6 block text-sm text-slate-600">
          Self-assessed score
          <div className="mt-3 flex items-center gap-4">
            <input
              type="range" min={0} max={100} step={1}
              value={value ?? 50}
              onChange={(e) => setValue(Number(e.target.value))}
              className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-indigo-600"
            />
            <input
              type="number" min={0} max={100}
              value={value ?? ""}
              placeholder="—"
              onChange={(e) => {
                const raw = e.target.value;
                if (raw === "") { setScores(({ [current.key]: _removed, ...rest }) => rest); return; }
                setValue(Math.max(0, Math.min(100, Number(raw))));
              }}
              className="w-20 rounded-md border bg-white px-3 py-2 text-sm"
            />
          </div>
        </label>

        {value !== undefined && (
          <p className={`mt-3 text-sm ${bandFor(value).tone}`}>
            {bandFor(value).label}
            {value < 55 && " — this dimension will show up as a gap in your roadmap."}
          </p>
        )}
        {value === undefined && (
          <p className="mt-3 text-sm text-slate-400">Not answered yet. Unanswered dimensions are simply left out of the submission.</p>
        )}
      </section>

      <section className="flex items-start gap-3 rounded-lg border bg-slate-50 p-4">
        <Lock className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
        <p className="text-sm text-slate-600">
          Scores are stored against your institution only and are visible to your TPO in aggregate.
          They are used as deterministic model inputs — no free-text answers are collected on this screen.
        </p>
      </section>

      <div className="flex flex-wrap items-center gap-2">
        <Button variant="outline" onClick={() => setIndex((i) => Math.max(0, i - 1))} disabled={index === 0}>
          <ChevronLeft className="mr-2 h-4 w-4" />Previous
        </Button>
        {index < DIMENSIONS.length - 1 ? (
          <Button onClick={() => setIndex((i) => Math.min(DIMENSIONS.length - 1, i + 1))}>
            Next: {DIMENSIONS[index + 1].title}<ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        ) : (
          <Button onClick={() => setReviewing(true)} disabled={answered.size === 0}>
            Review &amp; submit<ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        )}
        <Button variant="outline" onClick={() => setReviewing(true)} disabled={answered.size === 0} className="ml-auto">
          Skip to review ({answered.size}/{DIMENSIONS.length})
        </Button>
      </div>

      <p className="text-sm text-slate-500">
        Previous assessments recorded: {history.data?.results.length ?? 0}.{" "}
        <Link className="text-indigo-600" to="/student/profile">Back to profile</Link>
      </p>
    </section>
  );
}
