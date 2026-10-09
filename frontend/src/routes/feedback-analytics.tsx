import { createFileRoute } from "@tanstack/react-router";
import { FarmerFeedbackDashboard } from "@/features/farmerFeedback/FarmerFeedbackDashboard";

export const Route = createFileRoute("/feedback-analytics")({
  component: RouteComponent,
});

function RouteComponent() {
  return (
    <div className="flex-1 min-h-screen bg-slate-50/50">
      <FarmerFeedbackDashboard />
    </div>
  );
}
