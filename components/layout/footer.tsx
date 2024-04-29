export default function Footer() {
  return (
    <div className="absolute w-full py-5 text-center">
      <p className="text-gray-500">
        A project by{" "}
        <a
          className="font-semibold text-gray-600 underline-offset-4 transition-colors hover:underline"
          href="https://www.linkedin.com/in/steph-tien-ng"
          target="_blank"
          rel="noopener noreferrer"
        >
          Stephanie Ng
        </a>
        {", "}
        <a
          className="font-semibold text-gray-600 underline-offset-4 transition-colors hover:underline"
          href="https://www.linkedin.com/in/chrislevn/"
          target="_blank"
          rel="noopener noreferrer"
        >
          Chris Le
        </a>
        {", "}
        <a
          className="font-semibold text-gray-600 underline-offset-4 transition-colors hover:underline"
          href="#"
          target="_blank"
          rel="noopener noreferrer"
        >
          Long Nguyen
        </a>
        {", "}
        <a
          className="font-semibold text-gray-600 underline-offset-4 transition-colors hover:underline"
          href="https://www.linkedin.com/in/tranvinhlong/"
          target="_blank"
          rel="noopener noreferrer"
        >
          Long Tran
        </a>
      </p>
    </div>
  );
}
