// Outside timer for the weekly run. GitHub's own schedule started late or not at all on three Mondays in a row
// (12, 19 and 26 October 2026), so Netlify starts the GitHub workflow "Weekly ledger" as well, on Mondays at
// 13:11 and 14:11 UTC: one of the two is 9:11 a.m. US Eastern in summer, the other in winter.
//
// The function decides nothing about the data. It only asks GitHub to start the workflow with the switch
// "external" on. scripts/run.py then applies the same rule as for GitHub's schedule: it writes only on a Monday
// from 9:00 a.m. ET, only if this Monday's weekly run does not exist yet, and labels the run "external schedule".
// At any other time the started workflow ends without writing, so "Run now" in the Netlify UI is a safe test.
//
// Environment (Netlify > Site configuration > Environment variables, scope Functions):
//   GITHUB_DISPATCH_TOKEN   fine-grained token for this repository only, permission "Actions: Read and write"
//   LEDGER_DISPATCH_DRY_RUN "true" = send nothing; only check that the token can see the workflow and report
//                           what would be sent

const REPO = "pantaleonfassbender-coder/The-Promise-Ledger";
const WORKFLOW = "weekly.yml";
const REF = "main";
const API = `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}`;

export const config = { schedule: "11 13,14 * * 1" };

function easternNow(now) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "short", hour: "numeric", hourCycle: "h23", year: "numeric", month: "2-digit", day: "2-digit", minute: "2-digit" })
      .formatToParts(now).map(p => [p.type, p.value]));
  return { text: `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute} ET`, due: parts.weekday === "Mon" && Number(parts.hour) >= 9 };
}

function headers(token) {
  return {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "promise-ledger-weekly-dispatch",
  };
}

function reply(body, status = 200) {
  console.log(JSON.stringify(body));
  return new Response(JSON.stringify(body, null, 2), { status, headers: { "Content-Type": "application/json" } });
}

export default async (req) => {
  const now = new Date();
  const et = easternNow(now);
  const token = process.env.GITHUB_DISPATCH_TOKEN || "";
  const dryRun = (process.env.LEDGER_DISPATCH_DRY_RUN || "").toLowerCase() === "true";
  const payload = { ref: REF, inputs: { external: "true" } };
  const base = {
    utc: now.toISOString(),
    eastern: et.text,
    weekly_run_possible_now: et.due,
    note: et.due
      ? "Monday from 9:00 a.m. ET: run.py writes this run unless this Monday's weekly run already exists."
      : "Not Monday from 9:00 a.m. ET: the workflow will start and end without writing.",
  };

  if (!token) return reply({ ...base, dispatched: false, error: "GITHUB_DISPATCH_TOKEN is not set (redeploy after setting it)." }, 500);

  if (dryRun) {
    // Read-only check: can this token see the workflow? (Write access is only proven by a real dispatch.)
    const r = await fetch(API, { headers: headers(token) });
    return reply({ ...base, dry_run: true, dispatched: false, would_send: { url: `${API}/dispatches`, body: payload }, token_can_read_workflow: r.ok, github_status: r.status });
  }

  const r = await fetch(`${API}/dispatches`, { method: "POST", headers: { ...headers(token), "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  if (r.status === 204 || r.status === 200) return reply({ ...base, dispatched: true, github_status: r.status });
  const text = (await r.text()).slice(0, 300);
  return reply({ ...base, dispatched: false, github_status: r.status, github_message: text }, 502);
};
