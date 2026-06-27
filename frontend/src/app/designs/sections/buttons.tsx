import { Button } from "@/components/ui/button";

export default function ButtonsSection() {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">Buttons</h2>

      <div className="flex flex-wrap gap-3">
        <Button>Default</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="destructive">Destructive</Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button disabled>Disabled</Button>
        <Button className="w-40">Fixed width test</Button>
      </div>
    </section>
  );
}