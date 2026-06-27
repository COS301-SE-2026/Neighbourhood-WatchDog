import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function CardsSection() {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">Cards</h2>

      {/* Default card */}
      <Card>
        <CardHeader>
          <CardTitle>Default Card</CardTitle>
        </CardHeader>
        <CardContent>
          Base shadcn styling
        </CardContent>
      </Card>

    </section>
  );
}