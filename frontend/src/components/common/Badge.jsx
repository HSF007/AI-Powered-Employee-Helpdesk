import { slug } from "../../utils/format";

export default function Badge({ value, kind = "status", emptyLabel = "Unassigned", prefix }) {
  const label = value ?? emptyLabel;
  const tone = value ? slug(value) : "none";
  return (
    <span className={`badge badge-${kind} tone-${tone}`}>
      {prefix ? `${prefix}: ` : ""}
      {label}
    </span>
  );
}