import { CallSummaryView } from "@/components/call-summary";

export default async function Page({
  params,
}: {
  params: Promise<{ callId: string }>;
}) {
  const { callId } = await params;
  return <CallSummaryView callId={callId} />;
}
