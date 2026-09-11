import { FormEvent, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { Award, BookOpen, Briefcase, FileUp, GraduationCap, Sparkles, Upload } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { Certification, Experience, Profile, StudentSkill } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Error } from "@/pages/AuthPages";

const input = "w-full rounded-md border bg-white px-3 py-2 text-sm";
const label = "block text-sm text-slate-600";
const get = <T,>(path: string) => async () => (await api.get<T>(path)).data;

/** Fields that feed the readiness model, with the ranges the API validates against. */
const ACADEMIC_FIELDS = [
  { name: "cgpa", title: "CGPA", max: 10, suffix: "/ 10" },
  { name: "tenth_percentage", title: "10th percentage", max: 100, suffix: "%" },
  { name: "twelfth_percentage", title: "12th percentage", max: 100, suffix: "%" },
] as const;

const DIAGNOSTIC_FIELDS = [
  { name: "aptitude_score", title: "Aptitude score", max: 100, suffix: "%" },
  { name: "communication_rating", title: "Communication rating", max: 10, suffix: "/ 10" },
  { name: "extracurricular_score", title: "Extracurricular score", max: 100, suffix: "%" },
] as const;

/**
 * Completion is measured against the ten fields the model actually consumes, so
 * the ring reflects prediction readiness rather than a cosmetic percentage.
 */
function completionOf(profile: Profile) {
  const filled = [
    profile.cohort, profile.department,
    Number(profile.cgpa) > 0 ? "y" : "",
    Number(profile.tenth_percentage) > 0 ? "y" : "",
    Number(profile.twelfth_percentage) > 0 ? "y" : "",
    Number(profile.aptitude_score) > 0 ? "y" : "",
    Number(profile.communication_rating) > 0 ? "y" : "",
    Number(profile.extracurricular_score) > 0 ? "y" : "",
    profile.skills.length ? "y" : "",
    profile.experiences.length ? "y" : "",
  ].filter(Boolean).length;
  return Math.round((filled / 10) * 100);
}

function CompletionRing({ percent }: { percent: number }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const tone = percent >= 80 ? "stroke-emerald-500" : percent >= 50 ? "stroke-amber-500" : "stroke-rose-500";
  return (
    <div className="relative h-32 w-32 shrink-0">
      <svg className="h-32 w-32 -rotate-90" viewBox="0 0 128 128">
        <circle cx="64" cy="64" r={radius} className="fill-none stroke-slate-200" strokeWidth="12" />
        <circle
          cx="64" cy="64" r={radius}
          className={`fill-none ${tone} transition-[stroke-dashoffset] duration-700`}
          strokeWidth="12" strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - (percent / 100) * circumference}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-slate-900">{percent}%</span>
        <span className="text-xs text-slate-500">complete</span>
      </div>
    </div>
  );
}

function Card({ icon: Icon, title, hint, children }: { icon: typeof BookOpen; title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border bg-white p-5">
      <div className="mb-4 flex items-start gap-3">
        <span className="rounded-md bg-indigo-50 p-2"><Icon className="h-4 w-4 text-indigo-600" /></span>
        <div>
          <h2 className="font-semibold text-slate-900">{title}</h2>
          {hint && <p className="text-sm text-slate-500">{hint}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

function ScoreBar({ title, value, max, suffix }: { title: string; value: number; max: number; suffix: string }) {
  const percent = Math.min(100, Math.round((value / max) * 100));
  const tone = percent >= 75 ? "bg-emerald-500" : percent >= 50 ? "bg-amber-500" : "bg-rose-500";
  return (
    <div>
      <div className="flex items-baseline justify-between text-sm">
        <span className="text-slate-600">{title}</span>
        <span className="font-semibold text-slate-900">{value} <span className="font-normal text-slate-400">{suffix}</span></span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-slate-100">
        <div className={`h-2 rounded-full ${tone}`} style={{ width: `${percent}%` }} />
      </div>
      {percent < 60 && <p className="mt-1 text-xs text-amber-700">Below placement benchmark — prep recommended.</p>}
    </div>
  );
}

const PROFICIENCY_TONE: Record<string, string> = {
  expert: "bg-emerald-50 text-emerald-700",
  advanced: "bg-emerald-50 text-emerald-700",
  intermediate: "bg-amber-50 text-amber-700",
  beginner: "bg-slate-100 text-slate-600",
};

function SkillRow({ skill }: { skill: StudentSkill }) {
  return (
    <li className="flex flex-wrap items-center gap-2 border-b py-2 last:border-b-0">
      <span className="font-medium text-slate-800">{skill.skill.name}</span>
      <span className="text-xs text-slate-400">{skill.skill.category}</span>
      <span className={`ml-auto rounded px-2 py-0.5 text-xs capitalize ${PROFICIENCY_TONE[skill.proficiency] ?? "bg-slate-100 text-slate-600"}`}>
        {skill.proficiency}
      </span>
      {skill.source === "assessment" && (
        <span className="rounded bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700">Assessment verified</span>
      )}
    </li>
  );
}

export function StudentProfilePage() {
  const cache = useQueryClient();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const profile = useQuery({ queryKey: ["profile"], queryFn: get<Profile>("/v1/students/me/profile/") });
  const invalidate = () => { void cache.invalidateQueries({ queryKey: ["profile"] }); void cache.invalidateQueries({ queryKey: ["prediction"] }); };

  const save = useMutation({
    mutationFn: (body: Record<string, unknown>) => api.patch("/v1/students/me/profile/", body),
    onSuccess: () => { invalidate(); setNotice("Profile saved."); },
    onError: (e) => setError(errorMessage(e)),
  });

  const saveAndRecalculate = useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      await api.patch("/v1/students/me/profile/", body);
      await api.post("/v1/predictions/", {});
    },
    onSuccess: () => { invalidate(); navigate("/student"); },
    onError: (e) => setError(errorMessage(e)),
  });

  const importCsv = useMutation({
    mutationFn: (file: File) => {
      const body = new FormData();
      body.append("file", file);
      return api.post("/v1/students/me/import-csv/", body, { headers: { "Content-Type": "multipart/form-data" } });
    },
    onSuccess: () => { invalidate(); setNotice("CSV imported."); },
    onError: (e) => setError(errorMessage(e)),
  });

  const addCertification = useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post("/v1/students/me/certifications/", body),
    onSuccess: () => { invalidate(); setNotice("Certification added."); },
    onError: (e) => setError(errorMessage(e)),
  });

  const addExperience = useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post("/v1/students/me/experiences/", body),
    onSuccess: () => { invalidate(); setNotice("Experience added."); },
    onError: (e) => setError(errorMessage(e)),
  });

  if (profile.isLoading) return <p>Loading your profile…</p>;
  if (profile.isError) return <Error text={errorMessage(profile.error)} />;
  const p = profile.data!;

  const formBody = (form: HTMLFormElement) => Object.fromEntries(new FormData(form)) as Record<string, string>;

  function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setNotice("");
    save.mutate(formBody(event.currentTarget));
  }

  function onSaveAndRecalculate() {
    const form = document.getElementById("profile-form") as HTMLFormElement | null;
    if (!form) return;
    setError(""); setNotice("");
    saveAndRecalculate.mutate(formBody(form));
  }

  function onAddCertification(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setNotice("");
    const body = formBody(event.currentTarget);
    addCertification.mutate({ ...body, earned_at: body.earned_at || null });
    event.currentTarget.reset();
  }

  function onAddExperience(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setNotice("");
    const body = formBody(event.currentTarget);
    addExperience.mutate({ ...body, duration_months: Number(body.duration_months || 0), metadata: {} });
    event.currentTarget.reset();
  }

  const percent = completionOf(p);
  const byKind = (kind: string) => p.experiences.filter((e: Experience) => e.kind === kind);

  return (
    <section className="space-y-6 pb-24">
      <div>
        <p className="text-sm font-medium text-indigo-600">Student workspace</p>
        <h1 className="text-3xl font-bold">Employability profile</h1>
      </div>

      {error && <Error text={error} />}
      {notice && <p role="status" className="rounded bg-emerald-50 p-2 text-sm text-emerald-700">{notice}</p>}

      <section className="flex flex-wrap items-center gap-6 rounded-lg border bg-white p-5">
        <CompletionRing percent={percent} />
        <div className="min-w-[12rem] flex-1">
          <h2 className="font-semibold text-slate-900">Profile completion</h2>
          <p className="mt-1 text-sm text-slate-500">
            Measured across the ten fields the readiness model consumes. A prediction run on an
            incomplete profile is not meaningful, so finish these before recalculating.
          </p>
          <p className="mt-2 text-sm text-slate-600">
            {p.department || "No department set"}{p.cohort ? ` · ${p.cohort}` : ""}
          </p>
        </div>
        <div className="flex flex-col gap-2">
          <input
            ref={fileRef} type="file" accept=".csv" className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) importCsv.mutate(f); e.target.value = ""; }}
          />
          <Button type="button" variant="outline" onClick={() => fileRef.current?.click()} disabled={importCsv.isPending}>
            <Upload className="mr-2 h-4 w-4" />{importCsv.isPending ? "Importing…" : "Import CSV"}
          </Button>
          <p className="max-w-[13rem] text-xs text-slate-500">
            One data row, UTF-8. Columns matching profile fields are applied; a <code>skills</code> column adds catalogue skills.
          </p>
        </div>
      </section>

      <form id="profile-form" onSubmit={onSave} className="space-y-6">
        <Card icon={GraduationCap} title="Academic registry" hint="Self-reported and validated server-side against the declared ranges.">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className={label}>Cohort
              <input className={input} name="cohort" defaultValue={p.cohort ?? ""} placeholder="e.g. 2026" />
            </label>
            <label className={label}>Department
              <input className={input} name="department" defaultValue={p.department ?? ""} placeholder="e.g. Computer Science" />
            </label>
            {ACADEMIC_FIELDS.map((field) => (
              <label key={field.name} className={label}>{field.title} <span className="text-slate-400">({field.suffix})</span>
                <input className={input} name={field.name} type="number" step="0.01" min="0" max={field.max} defaultValue={p[field.name] ?? ""} />
              </label>
            ))}
            <label className={label}>Current backlogs
              <input className={input} name="current_backlogs" type="number" min="0" defaultValue={p.current_backlogs ?? 0} />
            </label>
            <label className={label}>Backlog history
              <input className={input} name="history_of_backlogs" type="number" min="0" defaultValue={p.history_of_backlogs ?? 0} />
            </label>
          </div>
          <p className="mt-3 text-sm">
            {Number(p.current_backlogs) === 0
              ? <span className="text-emerald-700">No active backlogs.</span>
              : <span className="text-rose-700">{p.current_backlogs} active backlog(s) — a strong negative driver in the model.</span>}
          </p>
        </Card>

        <Card icon={Sparkles} title="Aptitude &amp; communication" hint="These feed the readiness model directly alongside your assessment scores.">
          <div className="grid gap-4 sm:grid-cols-3">
            {DIAGNOSTIC_FIELDS.map((field) => (
              <label key={field.name} className={label}>{field.title} <span className="text-slate-400">({field.suffix})</span>
                <input className={input} name={field.name} type="number" step="0.01" min="0" max={field.max} defaultValue={p[field.name] ?? ""} />
              </label>
            ))}
          </div>
          <div className="mt-4 space-y-3">
            {DIAGNOSTIC_FIELDS.map((field) => (
              <ScoreBar key={field.name} title={field.title} value={Number(p[field.name] ?? 0)} max={field.max} suffix={field.suffix} />
            ))}
          </div>
        </Card>
      </form>

      <Card icon={BookOpen} title="Technical skills" hint="Skills are added through CSV import or verified by assessment; there is no public skill catalogue endpoint to pick from yet.">
        {p.skills.length ? (
          <ul>{p.skills.map((s) => <SkillRow key={s.id} skill={s} />)}</ul>
        ) : (
          <p className="text-sm text-slate-500">No skills recorded yet. Import a CSV with a <code>skills</code> column to add them.</p>
        )}
      </Card>

      <Card icon={Briefcase} title="Experience &amp; portfolio" hint="Internships, projects, open source, and research each count separately in the feature snapshot.">
        <div className="grid gap-4 sm:grid-cols-2">
          {["internship", "project", "open_source", "research"].map((kind) => (
            <div key={kind} className="rounded border p-3">
              <p className="text-sm font-medium capitalize text-slate-700">{kind.replace("_", " ")} ({byKind(kind).length})</p>
              {byKind(kind).length ? (
                <ul className="mt-1 space-y-1">
                  {byKind(kind).map((e) => (
                    <li key={e.id} className="text-sm text-slate-600">
                      {e.title}
                      <span className="text-slate-400"> · {e.complexity} · {e.duration_months} mo</span>
                    </li>
                  ))}
                </ul>
              ) : <p className="mt-1 text-sm text-slate-400">None recorded.</p>}
            </div>
          ))}
        </div>
        <form onSubmit={onAddExperience} className="mt-4 grid gap-3 sm:grid-cols-5">
          <select className={input} name="kind" defaultValue="project">
            {["project", "internship", "open_source", "research"].map((k) => (
              <option key={k} value={k}>{k.replace("_", " ")}</option>
            ))}
          </select>
          <input className={input} name="title" placeholder="Title" required />
          <select className={input} name="complexity" defaultValue="medium">
            {["low", "medium", "high"].map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input className={input} name="duration_months" type="number" min="0" placeholder="Months" />
          <Button type="submit" variant="outline" disabled={addExperience.isPending}>Add</Button>
        </form>
      </Card>

      <Card icon={Award} title="Certifications" hint="Counted as a feature in the readiness snapshot.">
        {p.certifications.length ? (
          <ul className="mb-4">
            {p.certifications.map((c: Certification) => (
              <li key={c.id} className="flex flex-wrap items-center gap-2 border-b py-2 last:border-b-0">
                <span className="font-medium text-slate-800">{c.name}</span>
                <span className="text-sm text-slate-500">{c.issuer}</span>
                {c.earned_at && <span className="ml-auto text-xs text-slate-400">{c.earned_at}</span>}
              </li>
            ))}
          </ul>
        ) : <p className="mb-4 text-sm text-slate-500">No certifications recorded yet.</p>}
        <form onSubmit={onAddCertification} className="grid gap-3 sm:grid-cols-4">
          <input className={input} name="name" placeholder="Certification name" required />
          <input className={input} name="issuer" placeholder="Issuer" required />
          <input className={input} name="earned_at" type="date" />
          <Button type="submit" variant="outline" disabled={addCertification.isPending}>Add</Button>
        </form>
      </Card>

      <div className="fixed inset-x-0 bottom-0 border-t bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-6 py-3">
          <p className="text-sm text-slate-500">
            {percent < 100 ? `${100 - percent}% of model inputs still empty.` : "All model inputs complete."}
          </p>
          <div className="ml-auto flex flex-wrap gap-2">
            <Button type="submit" form="profile-form" variant="outline" disabled={save.isPending}>
              {save.isPending ? "Saving…" : "Save profile"}
            </Button>
            <Button type="button" variant="outline" asChild>
              <Link to="/student/assessment"><FileUp className="mr-2 h-4 w-4" />Take assessment</Link>
            </Button>
            <Button type="button" onClick={onSaveAndRecalculate} disabled={saveAndRecalculate.isPending}>
              {saveAndRecalculate.isPending ? "Recalculating…" : "Save & recalculate readiness"}
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
