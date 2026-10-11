import { ResidentDetail } from "@/components/resident-detail";

export default async function Page({
  params,
}: {
  params: Promise<{ residentId: string }>;
}) {
  const { residentId } = await params;
  return <ResidentDetail id={residentId} />;
}
