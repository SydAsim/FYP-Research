import { EvaluationRunDetail } from "@/components/evaluation";

export default async function Page({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = await params;
  return <EvaluationRunDetail id={runId} />;
}
