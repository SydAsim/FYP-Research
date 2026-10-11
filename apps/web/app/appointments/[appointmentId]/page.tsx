import { AppointmentDetail } from "@/components/appointment-detail";

export default async function Page({
  params,
}: {
  params: Promise<{ appointmentId: string }>;
}) {
  const { appointmentId } = await params;
  return <AppointmentDetail id={appointmentId} />;
}
