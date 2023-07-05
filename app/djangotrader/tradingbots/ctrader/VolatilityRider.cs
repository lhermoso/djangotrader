using System;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;
using cAlgo.Indicators;
using System.Collections.Generic;







namespace cAlgo
{
    [Robot(TimeZone = TimeZones.ESouthAmericaStandardTime, AccessRights = AccessRights.FullAccess)]
    public class Rider : Robot
    {
        [Parameter("Quantidade (Lots)", DefaultValue = 0.5, MinValue = 0.01, Step = 5)]
        public double Quantity { get; set; }
        [Parameter("Take Profit Pips", DefaultValue = 5, MinValue = 0.75, Step = 0.1)]
        public double TakeProfit { get; set; }
        [Parameter("BB Min Distance", DefaultValue = 8, MinValue = 1, Step = 1)]
        public int BBDistance { get; set; }
        [Parameter("BB Period", DefaultValue = 20, MinValue = 2, Step = 1)]
        public int BBPeriod { get; set; }
        [Parameter("BB Deviations", DefaultValue = 2.1, MinValue = 0.5, Step = 0.1)]
        public double BBDeviations { get; set; }
        [Parameter("DayLight SVT", DefaultValue = true)]
        public bool DST { get; set; }
        [Parameter("1 = Long ; 2 = Short ; 3 = Both", DefaultValue = 3, MinValue = 1, MaxValue = 3, Step = 2)]
        public int Side { get; set; }


        private string VR_label;
        private bool VR_issellfilled, VR_isbuyfilled;
        BollingerBands VR_UpperBand, VR_BottomBand;




        protected override void OnStart()
        {


            VolatilityRider_Initializer();
            Positions.Opened += Positions_Opened;
            Positions.Closed += Positions_Closed;
            if (canITrade())
                VR_placeOrders();
            VR_init_Stops();

        }



        protected override void OnTick()
        {
            VR_OnTick();
        }


        protected override void OnBar()
        {

            VR_OnBar();
        }

        protected override void OnStop()
        {

            cancelOrders(VR_label);
        }

        private void VolatilityRider_Initializer()
        {
            //Initialize Indicators and Variables for Volatility Rider Strategy
            VR_UpperBand = Indicators.BollingerBands(MarketSeries.High, BBPeriod, BBDeviations, MovingAverageType.Simple);
            VR_BottomBand = Indicators.BollingerBands(MarketSeries.Low, BBPeriod, BBDeviations, MovingAverageType.Simple);
            VR_label = "VolatilityRider" + Symbol.Code + TimeFrame.ToString();
            VR_issellfilled = false;
            VR_isbuyfilled = false;





        }

        // Trade management - INIT//

        private void VR_placeOrders()
        {
            //Place order for Volatilty Rider Strategy

            double sellprice_ = sellprice();
            double buyprice_ = buyprice();
            if (bandsdistance() < BBDistance)
                return;
            if (MarketSeries.Close.LastValue < sellprice_ && (Side == 2 || Side == 3))
                PlaceLimitOrderAsync(TradeType.Sell, Symbol, getLot(TradeType.Sell, VR_label), sellprice_, VR_label, null, TakeProfit);

            if (MarketSeries.Close.LastValue > buyprice_ && (Side == 1 || Side == 3))
                PlaceLimitOrderAsync(TradeType.Buy, Symbol, getLot(TradeType.Buy, VR_label), buyprice_, VR_label, null, TakeProfit);
        }


        private void VR_modifyOrders()
        {
            // Modify Order for Volatility Rider strategy
            double sellprice_ = sellprice();
            double buyprice_ = buyprice();
            /*  if (hu.Result.LastValue > 0.5)
                cancelOrders(VR_label);*/
            foreach (var order in PendingOrders)
            {
                if (order.Label == VR_label)
                {
                    if (order.TradeType == TradeType.Sell && order.TargetPrice < sellprice_ && !VR_issellfilled)
                    {

                        if (Symbol.Ask < sellprice_)
                            ModifyPendingOrderAsync(order, order.Volume, sellprice_, order.StopLoss, TakeProfit, order.ExpirationTime);
                        else if (Symbol.Ask > sellprice_)                        /* + Symbol.PipSize * 0.1*/
                        {
                            cancel_orders_by_side(VR_label, TradeType.Sell, VR_label);

                        }

                    }
                    else if (order.TradeType == TradeType.Buy && order.TargetPrice > buyprice_ && !VR_isbuyfilled)
                    {
                        if (Symbol.Bid > buyprice_)
                            ModifyPendingOrderAsync(order, order.Volume, buyprice_, order.StopLoss, TakeProfit, order.ExpirationTime);
                        else if (Symbol.Bid < buyprice_)
                        {
                            cancel_orders_by_side(VR_label, TradeType.Buy, VR_label);
                        }
                    }
                }
            }
        }
        private void VR_init_Stops()
        {
            VR_setStops(TradeType.Sell);
            VR_setStops(TradeType.Buy);
        }
        private void VR_setStops(TradeType tradetype)
        {
            // TakeProfit Setter for Volatility Rider Strategy
            string label = VR_label;

            if (Positions.Count == 0)
                return;

            double entryPrice = 0, totalQuantity = 0;



            foreach (var position in Positions)
            {
                if (position.Label != label)
                    continue;
                if (position.TradeType == tradetype && position.SymbolCode == Symbol.Code && position.Label == label)
                {
                    entryPrice += (position.EntryPrice * position.Quantity);
                    totalQuantity += position.Quantity;
                }

            }

            double takeprofit = getTakeProfit(tradetype, label);

            entryPrice /= totalQuantity;

            foreach (var position in Positions)
            {
                if (position.Label != label)
                    continue;
                if (position.SymbolCode == Symbol.Code && position.Label == label && position.TradeType == tradetype)
                {
                    double? TakeProfit = entryPrice;
                    TakeProfit += tradetype == TradeType.Buy ? (takeprofit * Symbol.PipSize) : -(takeprofit * Symbol.PipSize);
                    ModifyPosition(position, position.StopLoss, TakeProfit);

                }
            }
        }


        private void cancel_orders_by_side(string Label, TradeType tradeType, string label)
        {
            // Cancel order by side and label
            foreach (var order in PendingOrders)
            {
                if (order.Label == label && order.TradeType == tradeType)
                    CancelPendingOrderAsync(order);
            }
        }

        private void cancelOrders(string label)
        {
            foreach (var order in PendingOrders)
            {
                if (order.Label == label)
                    CancelPendingOrderAsync(order);
            }

        }


        private bool canITrade()
        {
            // Return if the bot should trade or not.. on time base



            if (isHoliday())
                return false;
            int inicio = 22, fim = 18;
            if (DST)
            {
                inicio = 23;
                fim = 19;
            }
            return Server.Time.Hour >= fim && Server.Time.Hour < inicio ? false : true;
        }

        private bool isHoliday()
        {

            int day = MarketSeries.OpenTime.LastValue.Day;
            int month = MarketSeries.OpenTime.LastValue.Month;
            if (day == 2 && month == 1)
                // Ano Novo
                return true;
            if (day == 16 && month == 1)
                // Martin Luther King Jr. Day
                return true;
            if (day == 20 && month == 2)
                // Dia do Presidente
                return true;
            if (day == 14 && month == 4)
                // Sexta-feira santa
                return true;
            if (day == 29 && month == 5)
                // Memorial Day
                return true;
            if ((day == 3 || day == 4) && month == 7)
                // Independencia
                return true;
            if (day == 4 && month == 9)
                // Labor Day
                return true;
            if (day == 9 && month == 10)
                // Columbus Day
                return true;
            if (day == 11 && month == 11)
                // Columbus Day
                return true;
            if ((day == 23 || day == 24) && month == 11)
                // Thanksgiving Day
                return true;
            if ((day == 24 || day == 25) && month == 12)
                // Natal
                return true;

            return false;
        }

        private int numberOfPositions(TradeType tradetype, string label)
        {
            //Return Number of open positions

            int numberpositions = 0;
            foreach (var pos in Positions)
                if (pos.Label == label && pos.TradeType == tradetype)
                    numberpositions++;
            return numberpositions;


        }

        private double getTakeProfit(TradeType tradetype, string label)
        {
            // Return Profit to New position
                        /*  if (label == VR_label)
            {
                if (numberOfPositions(tradetype, label) == 1)
                    return 3;

                return TakeProfit;
            }*/
return TakeProfit;

        }
        // Trade management - END//
        //Helpers - INIT//





        private double upperband()
        {
            return VR_UpperBand.Top.LastValue;
        }

        private double bottomband()
        {
            return VR_BottomBand.Bottom.LastValue;
        }


        private double buyprice()
        {
            return Math.Round(bottomband(), Symbol.Digits);
        }

        private double sellprice()
        {
            return Math.Round(upperband(), Symbol.Digits);
        }


        private double bandsdistance()
        {
            return Math.Round((upperband() - bottomband()) / Symbol.PipSize, Symbol.Digits);
        }

        private long getLot(TradeType tradetype, string label)
        {
            if (label.Equals(VR_label))
                return Symbol.QuantityToVolume(Quantity);
            return Symbol.QuantityToVolume(Quantity);
        }



        // Herlper - END //
        // Positions Events - Init//

        void Positions_Closed(PositionClosedEventArgs obj)
        {
            var position = obj.Position;
            VR_setStops(position.TradeType);

        }

        void Positions_Opened(PositionOpenedEventArgs obj)
        {
            var position = obj.Position;
            if (position.Label == VR_label)
            {
                if (position.TradeType == TradeType.Buy)
                    VR_isbuyfilled = true;
                else
                    VR_issellfilled = true;

                VR_setStops(position.TradeType);
            }
        }


        // Positions Events - End//


        //Strategys EVENTS

        private void VR_OnBar()
        {
            cancelOrders(VR_label);

            if (!canITrade())
                return;


            VR_placeOrders();
            VR_isbuyfilled = false;
            VR_issellfilled = false;

        }

        private void VR_OnTick()
        {
            VR_modifyOrders();
        }
    }
}