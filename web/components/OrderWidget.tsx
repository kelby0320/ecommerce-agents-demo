type OrderItem = {
  name: string;
  quantity: number;
  price: number;
};

export type Order = {
  order_id: string;
  items: OrderItem[];
  status: string;
  total: number;
  created_at: string;
};

export type OrderWidgetProps =
  | { order: Order; orders?: never; totalCount?: never }
  | { orders: Order[]; totalCount: number; order?: never };

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  processing: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  shipped: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  delivered: "bg-green-500/20 text-green-400 border-green-500/30",
  cancelled: "bg-red-500/20 text-red-400 border-red-500/30",
};

function OrderCard({ order }: { order: Order }) {
  const statusStyle =
    STATUS_STYLES[order.status] ??
    "bg-zinc-700/50 text-zinc-400 border-zinc-600";

  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-4 text-sm">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-base font-semibold text-zinc-100">
          {order.order_id}
        </span>
        <span
          className={`rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${statusStyle}`}
        >
          {order.status}
        </span>
      </div>

      <div className="mb-3 space-y-1">
        {order.items.map((item, i) => (
          <div key={i} className="flex justify-between text-zinc-400">
            <span>
              {item.quantity}× {item.name}
            </span>
            {item.price > 0 && (
              <span>${(item.price * item.quantity).toFixed(2)}</span>
            )}
          </div>
        ))}
      </div>

      {order.total > 0 && (
        <div className="mb-2 flex justify-between border-t border-zinc-700 pt-2 font-medium text-zinc-200">
          <span>Total</span>
          <span>${order.total.toFixed(2)}</span>
        </div>
      )}

      <div className="text-xs text-zinc-600">
        {new Date(order.created_at).toLocaleString()}
      </div>
    </div>
  );
}

export function OrderWidget(props: OrderWidgetProps) {
  if (props.orders) {
    return (
      <div className="w-full space-y-2">
        <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
          {props.totalCount} order{props.totalCount !== 1 ? "s" : ""}
        </div>
        {props.orders.map((order) => (
          <OrderCard key={order.order_id} order={order} />
        ))}
      </div>
    );
  }

  return <OrderCard order={props.order} />;
}
