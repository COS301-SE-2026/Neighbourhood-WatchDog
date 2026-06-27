import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function FeedbackSection() {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">Feedback</h2>

      <div className="flex gap-2">
        <Badge>Default</Badge>
        <Badge className="bg-green text-black">Success</Badge>
        <Badge className="bg-threat">Error</Badge>
      </div>

      <Button>Toast trigger test (manual)</Button>
    </section>
  );
}