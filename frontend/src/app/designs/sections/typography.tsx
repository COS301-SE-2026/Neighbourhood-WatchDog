export default function TypographySection() {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">Typography</h2>

      <div className="space-y-2">
        <h1 className="text-[3rem] font-bold">Heading 1</h1>
        <h2 className="text-[2rem] font-semibold">Heading 2</h2>
        <h3 className="text-[1.25rem] font-medium">Heading 3</h3>

        <p className="text-body text-muted-foreground">
          Body text using system token
        </p>

        <p className="text-sm text-muted-foreground">
          Small muted text
        </p>
      </div>
    </section>
  );
}