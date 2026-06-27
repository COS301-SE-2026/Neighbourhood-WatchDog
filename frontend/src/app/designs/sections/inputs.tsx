import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function InputsSection() {
  return (
    <section className="space-y-4 max-w-md">
      <h2 className="text-xl font-semibold">Inputs</h2>

      <div className="space-y-2">
        <Label>Email</Label>
        <Input placeholder="m@example.com" />
      </div>

      <div className="space-y-2">
        <Label>Disabled</Label>
        <Input disabled placeholder="Disabled input" />
      </div>
    </section>
  );
}