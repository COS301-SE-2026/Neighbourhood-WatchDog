export default function ColorsSection() {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">Colors</h2>

      <div className="grid grid-cols-4 gap-4">
        <ColorBox label="Background" className="bg-background" />
        <ColorBox label="Card" className="bg-card" />
        <ColorBox label="Muted" className="bg-muted" />
        <ColorBox label="Primary" className="bg-primary" />
        <ColorBox label="Border" className="bg-border" />
      </div>
    </section>
  );
}

function ColorBox({ label, className }: any) {
  return (
    <div className="space-y-2">
      <div className={`h-12 rounded-md border ${className}`} />
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}