import { LiveCall } from "@/components/live-call";

export default async function Page({
  params,
}: {
  params: Promise<{ callId: string }>;
}) {
  const { callId } = await params;
  return <LiveCall key={callId} callId={callId} />;
}
