import TypographySection from "./sections/typography";
import ColorsSection from "./sections/colors";
import ButtonsSection from "./sections/buttons";
import CardsSection from "./sections/cards";
import InputsSection from "./sections/inputs";
import FeedbackSection from "./sections/feedback";

export default function DesignSystemPage() {
  return (
    <div className="space-y-16 p-10">
      <h1 className="text-3xl font-semibold">Design System</h1>

      <TypographySection />
      <ColorsSection />
      <ButtonsSection />
      <CardsSection />
      <InputsSection />
      <FeedbackSection />
    </div>
  );
}