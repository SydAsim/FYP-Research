import { WorkflowTrace } from "@/components/workflow-trace";

export default async function Page({
  params,
}: {
  params: Promise<{ callId: string }>;
}) {
  const { callId } = await params;
  return <WorkflowTrace callId={callId} />;
}
